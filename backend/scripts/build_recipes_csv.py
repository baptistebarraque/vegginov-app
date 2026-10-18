"""Turn a generated recipe batch (JSON) into a CSV the importer will accept.

Run with:
    uv run python -m scripts.build_recipes_csv "../../CC0 DB/llm_generated/batch_01.json"
    uv run python -m scripts.build_recipes_csv <path> --output recettes.csv

Recipes drafted by a language model meet the import contract only if something
checks them, and the ways they fail are not equally loud — which is why this
validates before writing rather than letting the admin discover the problem at
upload time:

* **Fatal.** `protein_source` outside `RECIPE_PROTEIN_VOCABULARY`, `price_tier`
  outside 1..MAX_PRICE_TIER, a missing quantity while `servings` is set, or a
  `;`/`:` inside a name, quantity or instruction step. `parse_csv` is
  all-or-nothing, so any one of these rejects the entire file.
* **Silent.** An ingredient absent from `SOURCE_TO_FLAVORGRAPH` imports fine but
  is dropped from `ingredient_set_similarity` — logged, never raised — so the
  recipe quietly ranks worse forever. Only a check makes that visible.
* **Cosmetic.** Everything else (ingredient count, nutrition plausibility,
  ingredients listed but never used in a step) is reported as a warning and
  left to a human.

The last gate is `recipe_import_service.parse_csv` itself, so a file this script
writes is a file the web importer and `scripts.import_recipes_csv` accept.
Nothing is written unless every fatal check passes.
"""

import argparse
import csv
import io
import json
import logging
import re
import sys
import unicodedata
from pathlib import Path

from veggie_app.matching.flavorgraph import get_vector
from veggie_app.matching.substitution import RECIPE_PROTEIN_VOCABULARY
from veggie_app.services import recipe_import_service, recipe_service
from veggie_app.services.recipe_service import MAX_PRICE_TIER, DishStructureError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = False
_handler = logging.StreamHandler()
_handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(_handler)

# Allergen strings have to match what a user types in the preferences form
# exactly: services/recipe_service.py intersects the two sets with no
# normalisation, so "oeufs" or "Gluten" would silently never filter anything.
ALLOWED_ALLERGENS = {
    "gluten",
    "lactose",
    "oeuf",
    "fruits a coque",
    "arachide",
    "soja",
    "sesame",
    "moutarde",
    "sulfites",
    "celeri",
}

# Non-vegetarian items the closed ingredient vocabulary cannot catch, because
# they only ever appear in free instruction text.
NON_VEG_TEXT = re.compile(
    r"bouillon de (volaille|boeuf|bœuf|poule)|nuoc|sauce de poisson|"
    r"worcestershire|gélatine|présure animale|\blard\b|saindoux|anchois",
    re.I,
)

# Carried through to the CSV for later use but ignored by parse_csv, which only
# reads the columns it knows — see EXPORT_COLUMNS in recipe_import_service.
EXTRA_COLUMNS = ["image_query", "protein_source_raw", "is_vegan", "unmapped_ingredients"]

# Assumed rather than narrated ("saler", "assaisonner"), so excluding them from
# the "listed but never used" check keeps the genuine misses visible.
SEASONINGS = {
    "sel",
    "poivre",
    "sel de mer",
    "fleur de sel",
    "gros sel",
    "poivre blanc",
    "grains de poivre",
    "muscade",
    "piment d'espelette",
    "herbes de provence",
}

MIN_INGREDIENTS, MAX_INGREDIENTS = 6, 12
CAL_MIN, CAL_MAX = 250.0, 900.0
DENSITY_MAX = 12.0  # grams of protein per 100 kcal — above this is implausible


def strip_accents(text: str) -> str:
    """Accent-insensitive comparison helper. Only used for the checks below —
    never for the values written out, since get_vector's lookup is accent
    sensitive and the CSV has to keep the exact vocabulary spelling."""
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def _check_delimiters(recipe: dict, tag: str, errors: list[str], warnings: list[str]) -> None:
    """';' separates list items and ':' splits an ingredient name from its
    quantity, so either one inside a value corrupts the row's grammar."""
    if any(character in (recipe.get("title") or "") for character in ";:"):
        errors.append(f"{tag} : le titre contient ';' ou ':'")
    for step in recipe.get("instructions", []):
        if ";" in step:
            errors.append(f"{tag} : une étape contient ';' — {step[:60]!r}")
        if ":" in step:
            warnings.append(f"{tag} : une étape contient ':' (sans danger, mais à éviter)")


def _check_ingredients(recipe: dict, tag: str, errors: list[str], warnings: list[str]) -> None:
    ingredients = recipe.get("ingredients", [])
    if not ingredients:
        errors.append(f"{tag} : aucun ingrédient")
        return

    for item in ingredients:
        name, quantity = item.get("name", ""), item.get("quantity")
        if any(character in name for character in ";:"):
            errors.append(f"{tag} : l'ingrédient {name!r} contient ';' ou ':'")
        if not quantity:
            errors.append(f"{tag} : quantité manquante pour {name!r} (servings est renseigné)")
        elif any(character in quantity for character in ";:"):
            errors.append(f"{tag} : la quantité {quantity!r} contient ';' ou ':'")
        if get_vector(name) is None:
            errors.append(f"{tag} : {name!r} est absent du vocabulaire FlavorGraph")

    if not MIN_INGREDIENTS <= len(ingredients) <= MAX_INGREDIENTS:
        warnings.append(
            f"{tag} : {len(ingredients)} ingrédients (cible {MIN_INGREDIENTS}-{MAX_INGREDIENTS})"
        )


def _check_nutrition(recipe: dict, tag: str, warnings: list[str]) -> None:
    calories = recipe.get("calories_per_portion")
    protein_grams = recipe.get("protein_grams")
    if not isinstance(calories, int | float) or not CAL_MIN <= calories <= CAL_MAX:
        warnings.append(
            f"{tag} : calories_per_portion {calories!r} hors de {CAL_MIN:g}-{CAL_MAX:g}"
        )
    if isinstance(calories, int | float) and isinstance(protein_grams, int | float) and calories:
        density = protein_grams / calories * 100
        if density > DENSITY_MAX:
            warnings.append(f"{tag} : densité protéique {density:.1f} g/100 kcal peu plausible")


def _check_coherence(recipe: dict, tag: str, errors: list[str], warnings: list[str]) -> None:
    """A listed ingredient that no step ever uses is the most visible defect to
    whoever cooks the recipe, and nothing downstream would catch it."""
    joined = " ".join(recipe.get("instructions", []))

    hit = NON_VEG_TEXT.search(joined)
    if hit:
        errors.append(f"{tag} : ingrédient non végétarien dans les étapes — {hit.group(0)!r}")

    steps = strip_accents(joined.lower())
    unused = []
    for item in recipe.get("ingredients", []):
        name = item.get("name", "")
        if strip_accents(name.lower()) in SEASONINGS:
            continue
        head = strip_accents(name.lower()).split()[0].rstrip("s")
        if head and head not in steps:
            unused.append(name)
    if unused:
        warnings.append(f"{tag} : listé mais jamais utilisé dans une étape — {', '.join(unused)}")


def validate(recipes: list[dict]) -> tuple[list[str], list[str]]:
    """Returns (errors, warnings). Errors block the write, warnings don't."""
    errors: list[str] = []
    warnings: list[str] = []
    seen_titles: dict[str, int] = {}

    for index, recipe in enumerate(recipes, start=1):
        tag = f"recette {index} ({recipe.get('title', '<sans titre>')})"

        title = (recipe.get("title") or "").strip()
        if not title:
            errors.append(f"{tag} : titre vide")
        # Accent- and case-insensitive, since two titles differing only by an
        # accent would read as duplicates to a user even though the DB has no
        # unique constraint to stop them.
        key = strip_accents(title.lower())
        if key in seen_titles:
            errors.append(f"{tag} : titre en double, déjà vu recette {seen_titles[key]}")
        seen_titles[key] = index

        _check_delimiters(recipe, tag, errors, warnings)
        _check_ingredients(recipe, tag, errors, warnings)

        protein_source = recipe.get("protein_source")
        if protein_source not in RECIPE_PROTEIN_VOCABULARY:
            errors.append(
                f"{tag} : protein_source {protein_source!r} absent de RECIPE_PROTEIN_VOCABULARY"
            )

        price_tier = recipe.get("price_tier")
        if not (isinstance(price_tier, int) and 1 <= price_tier <= MAX_PRICE_TIER):
            errors.append(f"{tag} : price_tier {price_tier!r} hors de 1..{MAX_PRICE_TIER}")

        if recipe.get("servings") != 4:
            warnings.append(f"{tag} : servings vaut {recipe.get('servings')!r}, attendu 4")

        dish_types, cuisine = recipe.get("dish_types", []), recipe.get("cuisine")
        try:
            recipe_service.validate_dish_structure(dish_types, cuisine)
        except DishStructureError as exc:
            errors.append(f"{tag} : {exc}")
        if not dish_types or not cuisine:
            warnings.append(f"{tag} : dish_types/cuisine manquants (vue structure inactive)")

        for allergen in recipe.get("allergens", []):
            if allergen not in ALLOWED_ALLERGENS:
                errors.append(f"{tag} : allergène {allergen!r} hors de la liste autorisée")

        _check_nutrition(recipe, tag, warnings)
        _check_coherence(recipe, tag, errors, warnings)

    return errors, warnings


def to_rows(recipes: list[dict]) -> list[dict]:
    """Serialize to the same shape export_recipes_to_csv emits, so a file built
    here and a file downloaded from the admin export are interchangeable."""
    joiner = recipe_import_service.LIST_DELIMITER + " "
    rows = []
    for recipe in recipes:
        ingredients = joiner.join(
            f"{item['name']}{recipe_import_service.QUANTITY_DELIMITER}{item['quantity']}"
            for item in recipe["ingredients"]
        )
        rows.append(
            {
                "title": recipe["title"],
                "ingredients": ingredients,
                "allergens": joiner.join(recipe.get("allergens", [])),
                "prep_time_minutes": recipe.get("prep_time_minutes", ""),
                "servings": recipe.get("servings", ""),
                "protein_source": recipe.get("protein_source", ""),
                "protein_grams": recipe.get("protein_grams", ""),
                "calories_per_portion": recipe.get("calories_per_portion", ""),
                "price_tier": recipe.get("price_tier", ""),
                "dish_types": joiner.join(recipe.get("dish_types", [])),
                "cuisine": recipe.get("cuisine") or "",
                "instructions": joiner.join(recipe.get("instructions", [])),
                "image_query": recipe.get("image_query", ""),
                "protein_source_raw": recipe.get("protein_source_raw", ""),
                "is_vegan": str(recipe.get("is_vegan", False)).lower(),
                "unmapped_ingredients": joiner.join(recipe.get("unmapped_ingredients", [])),
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_path", type=Path, help="JSON recipe batch to convert")
    parser.add_argument(
        "--output", type=Path, default=None, help="CSV to write (default: alongside the JSON)"
    )
    args = parser.parse_args()

    if not args.json_path.is_file():
        logger.error("Fichier introuvable : %s", args.json_path)
        return 1

    recipes = json.loads(args.json_path.read_text(encoding="utf-8"))
    logger.info("%d recette(s) lue(s) dans %s.", len(recipes), args.json_path.name)

    errors, warnings = validate(recipes)
    for warning in warnings:
        logger.info("  ATTENTION %s", warning)
    for error in errors:
        logger.error("  ERREUR    %s", error)
    if errors:
        logger.error("%d erreur(s) — rien n'a été écrit.", len(errors))
        return 1

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=recipe_import_service.EXPORT_COLUMNS + EXTRA_COLUMNS)
    writer.writeheader()
    writer.writerows(to_rows(recipes))
    content = buffer.getvalue()

    # Final gate: the project's own parser, all-or-nothing like the real import.
    try:
        parsed = recipe_import_service.parse_csv(content)
    except recipe_import_service.CsvImportError as exc:
        for row_error in exc.errors:
            logger.error("  ligne %d : %s", row_error.row_number, row_error.message)
        return 1

    target = args.output or args.json_path.with_suffix(".csv")
    target.write_text(content, encoding="utf-8", newline="")
    logger.info("parse_csv a accepté les %d ligne(s).", len(parsed))
    logger.info("%d avertissement(s). Écrit dans %s.", len(warnings), target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
