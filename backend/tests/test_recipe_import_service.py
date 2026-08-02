import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from veggie_app.matching.embeddings import EMBEDDING_DIM
from veggie_app.models.recipe import Recipe
from veggie_app.services import recipe_import_service, recipe_service
from veggie_app.services.recipe_import_service import CsvImportError

VALID_CSV = (
    "title,ingredients,allergens,prep_time_minutes,servings,protein_source,protein_grams,"
    "instructions\n"
    "Curry de lentilles corail,lentilles corail:200g; lait de coco:200ml; curry:1 c.a.s,"
    "gluten,25,4,lentilles corail,15,Faire chauffer le lait de coco; Ajouter le curry\n"
    "Salade de quinoa,quinoa; tomates,,,,,,\n"
)


@pytest.fixture(autouse=True)
def _stub_embedding(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(recipe_service, "embed_text", lambda text: [0.0] * EMBEDDING_DIM)


def test_parse_csv_parses_valid_rows() -> None:
    rows = recipe_import_service.parse_csv(VALID_CSV)

    assert len(rows) == 2
    assert rows[0]["title"] == "Curry de lentilles corail"
    assert rows[0]["ingredients"] == [
        {"name": "lentilles corail", "quantity": "200g"},
        {"name": "lait de coco", "quantity": "200ml"},
        {"name": "curry", "quantity": "1 c.a.s"},
    ]
    assert rows[0]["allergens"] == ["gluten"]
    assert rows[0]["prep_time_minutes"] == 25
    assert rows[0]["servings"] == 4
    assert rows[0]["protein_source"] == "lentilles corail"
    assert rows[0]["protein_grams"] == 15.0
    assert rows[0]["instructions"] == ["Faire chauffer le lait de coco", "Ajouter le curry"]
    assert rows[1]["title"] == "Salade de quinoa"
    assert rows[1]["ingredients"] == [
        {"name": "quinoa", "quantity": None},
        {"name": "tomates", "quantity": None},
    ]
    assert rows[1]["allergens"] == []
    assert rows[1]["prep_time_minutes"] is None


def test_parse_csv_rejects_missing_required_column() -> None:
    with pytest.raises(CsvImportError) as exc_info:
        recipe_import_service.parse_csv("title,allergens\nSalade,gluten\n")

    assert exc_info.value.errors[0].row_number == 1
    assert "ingredients" in exc_info.value.errors[0].message


def test_parse_csv_rejects_empty_title() -> None:
    with pytest.raises(CsvImportError) as exc_info:
        recipe_import_service.parse_csv("title,ingredients\n,laitue\n")

    assert exc_info.value.errors[0].row_number == 2


def test_parse_csv_rejects_invalid_number() -> None:
    with pytest.raises(CsvImportError) as exc_info:
        recipe_import_service.parse_csv(
            "title,ingredients,prep_time_minutes\nSalade,laitue,pas-un-nombre\n"
        )

    assert exc_info.value.errors[0].row_number == 2
    assert "prep_time_minutes" in exc_info.value.errors[0].message


def test_parse_csv_reports_every_invalid_row_not_just_the_first() -> None:
    with pytest.raises(CsvImportError) as exc_info:
        recipe_import_service.parse_csv("title,ingredients\n,laitue\nSalade,\n")

    assert [error.row_number for error in exc_info.value.errors] == [2, 3]


def test_parse_csv_rejects_missing_quantity_when_servings_set() -> None:
    with pytest.raises(CsvImportError) as exc_info:
        recipe_import_service.parse_csv(
            "title,ingredients,servings\nSalade,laitue,2\n"
        )

    assert exc_info.value.errors[0].row_number == 2
    assert "laitue" in exc_info.value.errors[0].message


def test_parse_csv_allows_missing_quantity_without_servings() -> None:
    rows = recipe_import_service.parse_csv("title,ingredients\nSalade,laitue\n")

    assert rows[0]["ingredients"] == [{"name": "laitue", "quantity": None}]


def test_parse_csv_parses_calories_and_price_tier() -> None:
    rows = recipe_import_service.parse_csv(
        "title,ingredients,calories_per_portion,price_tier\nSalade,laitue,320,2\n"
    )

    assert rows[0]["calories_per_portion"] == 320.0
    assert rows[0]["price_tier"] == 2


def test_parse_csv_rejects_price_tier_out_of_range() -> None:
    with pytest.raises(CsvImportError) as exc_info:
        recipe_import_service.parse_csv(
            "title,ingredients,price_tier\nSalade,laitue,9\n"
        )

    assert exc_info.value.errors[0].row_number == 2
    assert "prix" in exc_info.value.errors[0].message


def test_export_round_trips_calories_and_price_tier(db_session: Session) -> None:
    recipe_service.create_recipe(
        db_session,
        title="Tofu grillé",
        ingredients=[{"name": "tofu", "quantity": None}],
        calories_per_portion=180.0,
        price_tier=2,
    )

    reparsed = recipe_import_service.parse_csv(
        recipe_import_service.export_recipes_to_csv(db_session)
    )

    assert reparsed[0]["calories_per_portion"] == 180.0
    assert reparsed[0]["price_tier"] == 2


def test_parse_csv_rejects_unknown_protein_source() -> None:
    with pytest.raises(CsvImportError) as exc_info:
        recipe_import_service.parse_csv(
            "title,ingredients,protein_source\nSalade,laitue,boeuf haché\n"
        )

    assert exc_info.value.errors[0].row_number == 2
    assert "boeuf haché" in exc_info.value.errors[0].message


def test_import_recipes_from_csv_persists_all_valid_rows(db_session: Session) -> None:
    recipes = recipe_import_service.import_recipes_from_csv(db_session, VALID_CSV)

    assert len(recipes) == 2
    stored_titles = db_session.execute(select(Recipe.title)).scalars().all()
    assert set(stored_titles) == {"Curry de lentilles corail", "Salade de quinoa"}


def test_import_recipes_from_csv_is_all_or_nothing(db_session: Session) -> None:
    csv_with_one_bad_row = "title,ingredients\nSalade,laitue\n,tomates\n"

    with pytest.raises(CsvImportError):
        recipe_import_service.import_recipes_from_csv(db_session, csv_with_one_bad_row)

    assert db_session.execute(select(Recipe)).scalars().all() == []


def test_export_recipes_to_csv_has_header_and_row_per_recipe(db_session: Session) -> None:
    recipe_import_service.import_recipes_from_csv(db_session, VALID_CSV)

    exported = recipe_import_service.export_recipes_to_csv(db_session)

    lines = exported.splitlines()
    assert lines[0] == (
        "title,ingredients,allergens,prep_time_minutes,servings,protein_source,"
        "protein_grams,calories_per_portion,price_tier,instructions"
    )
    assert len(lines) == 3  # header + two recipes


def test_export_recipes_to_csv_round_trips_through_import(db_session: Session) -> None:
    original = recipe_import_service.import_recipes_from_csv(db_session, VALID_CSV)
    exported = recipe_import_service.export_recipes_to_csv(db_session)

    reparsed = recipe_import_service.parse_csv(exported)

    by_title = {row["title"]: row for row in reparsed}
    curry = by_title["Curry de lentilles corail"]
    assert curry["ingredients"] == [
        {"name": "lentilles corail", "quantity": "200g"},
        {"name": "lait de coco", "quantity": "200ml"},
        {"name": "curry", "quantity": "1 c.a.s"},
    ]
    assert curry["allergens"] == ["gluten"]
    assert curry["prep_time_minutes"] == 25
    assert curry["servings"] == 4
    assert curry["protein_source"] == "lentilles corail"
    assert curry["protein_grams"] == 15.0
    assert curry["instructions"] == ["Faire chauffer le lait de coco", "Ajouter le curry"]

    salade = by_title["Salade de quinoa"]
    assert salade["ingredients"] == [
        {"name": "quinoa", "quantity": None},
        {"name": "tomates", "quantity": None},
    ]
    assert salade["allergens"] == []
    assert salade["prep_time_minutes"] is None
    assert len(original) == len(reparsed)


def test_export_formats_integral_protein_grams_without_decimal(db_session: Session) -> None:
    recipe_service.create_recipe(
        db_session,
        title="Tofu grillé",
        ingredients=[{"name": "tofu", "quantity": "200g"}],
        protein_grams=15.0,
    )

    exported = recipe_import_service.export_recipes_to_csv(db_session)

    assert ",15," in exported
    assert "15.0" not in exported


def test_export_escapes_commas_in_values(db_session: Session) -> None:
    recipe_service.create_recipe(
        db_session,
        title="Salade, verte",
        ingredients=[{"name": "laitue", "quantity": None}],
    )

    exported = recipe_import_service.export_recipes_to_csv(db_session)

    assert '"Salade, verte"' in exported
    assert recipe_import_service.parse_csv(exported)[0]["title"] == "Salade, verte"
