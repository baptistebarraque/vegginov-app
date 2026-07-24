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
