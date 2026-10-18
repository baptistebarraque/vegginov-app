"""Bulk recipe import from a CSV file (see docs/ARCHITECTURE.md "Bulk recipe
CSV import").

Every row is validated before anything is written to the database: if any
row is invalid, nothing is imported and every row's error is reported, so
the admin can fix the CSV and re-upload once instead of ending up with a
half-imported, hard-to-dedupe batch.
"""

import csv
import io
from dataclasses import dataclass

from sqlalchemy.orm import Session

from veggie_app.models.recipe import IngredientEntry, Recipe
from veggie_app.services import recipe_service

REQUIRED_COLUMNS = {"title", "ingredients"}
LIST_DELIMITER = ";"
QUANTITY_DELIMITER = ":"

# Column order for CSV export, chosen so a downloaded file matches the import
# template and can be re-uploaded through parse_csv unchanged.
EXPORT_COLUMNS = [
    "title",
    "ingredients",
    "allergens",
    "prep_time_minutes",
    "servings",
    "protein_source",
    "protein_grams",
    "calories_per_portion",
    "price_tier",
    "dish_types",
    "cuisine",
    "instructions",
]

# On write we join with "; " (delimiter + space) for readability; parse_csv
# strips whitespace around each item, so the space round-trips away on re-upload.
_LIST_JOINER = LIST_DELIMITER + " "


@dataclass
class RowError:
    row_number: int  # 1-based, counting the header as row 1 (matches what a spreadsheet shows)
    message: str


class CsvImportError(ValueError):
    def __init__(self, errors: list[RowError]) -> None:
        self.errors = errors
        super().__init__(f"{len(errors)} invalid row(s)")


def _split_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(LIST_DELIMITER) if item.strip()]


def _parse_ingredients(raw: str | None) -> list[IngredientEntry]:
    """Each ';'-separated item is 'name' or 'name:quantity', e.g.
    "riz:200g; lait de coco:200ml; curry" (quantity optional per item)."""
    entries: list[IngredientEntry] = []
    for item in _split_list(raw):
        name, _, quantity = item.partition(QUANTITY_DELIMITER)
        name = name.strip()
        if name:
            entries.append({"name": name, "quantity": quantity.strip() or None})
    return entries


def _parse_optional_int(raw: str | None, column: str) -> int | None:
    if raw is None or not raw.strip():
        return None
    try:
        return int(raw.strip())
    except ValueError:
        raise ValueError(
            f"la colonne '{column}' doit être un nombre entier (valeur reçue : {raw!r})"
        ) from None


def _parse_optional_float(raw: str | None, column: str) -> float | None:
    if raw is None or not raw.strip():
        return None
    try:
        return float(raw.strip())
    except ValueError:
        raise ValueError(
            f"la colonne '{column}' doit être un nombre (valeur reçue : {raw!r})"
        ) from None


def _parse_row(row: dict[str, str | None]) -> dict:
    title = (row.get("title") or "").strip()
    if not title:
        raise ValueError("la colonne 'title' est obligatoire")

    ingredients = _parse_ingredients(row.get("ingredients"))
    if not ingredients:
        raise ValueError("la colonne 'ingredients' doit contenir au moins un ingrédient")

    servings = _parse_optional_int(row.get("servings"), "servings")
    recipe_service.validate_ingredient_quantities(ingredients, servings)

    protein_source = (row.get("protein_source") or "").strip() or None
    recipe_service.validate_protein_source(protein_source)

    price_tier = _parse_optional_int(row.get("price_tier"), "price_tier")
    recipe_service.validate_price_tier(price_tier)

    dish_types = _split_list(row.get("dish_types"))
    cuisine = (row.get("cuisine") or "").strip() or None
    recipe_service.validate_dish_structure(dish_types, cuisine)

    return {
        "title": title,
        "ingredients": ingredients,
        "allergens": _split_list(row.get("allergens")),
        "prep_time_minutes": _parse_optional_int(row.get("prep_time_minutes"), "prep_time_minutes"),
        "servings": servings,
        "protein_source": protein_source,
        "protein_grams": _parse_optional_float(row.get("protein_grams"), "protein_grams"),
        "calories_per_portion": _parse_optional_float(
            row.get("calories_per_portion"), "calories_per_portion"
        ),
        "price_tier": price_tier,
        "dish_types": dish_types,
        "cuisine": cuisine,
        "instructions": _split_list(row.get("instructions")),
    }


def parse_csv(content: str) -> list[dict]:
    """Parse and validate every row, raising `CsvImportError` (carrying
    every row's error, not just the first) if any row is invalid — in that
    case nothing has been touched in the database yet."""
    reader = csv.DictReader(io.StringIO(content))
    if reader.fieldnames is None:
        raise CsvImportError([RowError(1, "le fichier CSV est vide")])

    missing_columns = REQUIRED_COLUMNS - set(reader.fieldnames)
    if missing_columns:
        raise CsvImportError(
            [
                RowError(
                    1,
                    "colonne(s) obligatoire(s) manquante(s) : "
                    + ", ".join(sorted(missing_columns)),
                )
            ]
        )

    parsed_rows = []
    errors = []
    for row_number, row in enumerate(reader, start=2):  # row 1 is the header
        try:
            parsed_rows.append(_parse_row(row))
        except ValueError as exc:
            errors.append(RowError(row_number, str(exc)))

    if errors:
        raise CsvImportError(errors)

    return parsed_rows


def import_recipes_from_csv(db: Session, content: str) -> list[Recipe]:
    parsed_rows = parse_csv(content)
    return [recipe_service.create_recipe(db, **row) for row in parsed_rows]


def _format_number(value: int | float | None) -> str:
    """Empty cell for None; integral floats (e.g. 15.0 protein_grams) render as
    '15' rather than '15.0' to match how an admin would type them."""
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _format_ingredients(ingredients: list[IngredientEntry]) -> str:
    items = []
    for ingredient in ingredients:
        name = ingredient["name"]
        quantity = ingredient.get("quantity")
        items.append(f"{name}{QUANTITY_DELIMITER}{quantity}" if quantity else name)
    return _LIST_JOINER.join(items)


def _recipe_to_row(recipe: Recipe) -> dict[str, str]:
    return {
        "title": recipe.title,
        "ingredients": _format_ingredients(recipe.ingredients),
        "allergens": _LIST_JOINER.join(recipe.allergens),
        "prep_time_minutes": _format_number(recipe.prep_time_minutes),
        "servings": _format_number(recipe.servings),
        "protein_source": recipe.protein_source or "",
        "protein_grams": _format_number(recipe.protein_grams),
        "calories_per_portion": _format_number(recipe.calories_per_portion),
        "price_tier": _format_number(recipe.price_tier),
        "dish_types": _LIST_JOINER.join(recipe.dish_types),
        "cuisine": recipe.cuisine or "",
        "instructions": _LIST_JOINER.join(recipe.instructions),
    }


def export_recipes_to_csv(db: Session) -> str:
    """Serialize every recipe to the same CSV format `parse_csv` accepts, so a
    downloaded export can be re-uploaded unchanged. Images aren't part of the
    CSV format (a cell can't hold binary data), so they're omitted here too."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=EXPORT_COLUMNS)
    writer.writeheader()
    for recipe in recipe_service.list_recipes(db):
        writer.writerow(_recipe_to_row(recipe))
    return output.getvalue()
