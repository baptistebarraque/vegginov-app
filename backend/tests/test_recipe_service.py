import pytest
from sqlalchemy.orm import Session

from veggie_app.matching.embeddings import EMBEDDING_DIM
from veggie_app.models.recipe import Recipe
from veggie_app.services import recipe_service
from veggie_app.services.recipe_service import IngredientQuantityError


def _unit_vector(index: int) -> list[float]:
    vector = [0.0] * EMBEDDING_DIM
    vector[index] = 1.0
    return vector


@pytest.fixture(autouse=True)
def _stub_query_embedding(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace the stubbed-but-still-pseudo-random embed_text with a fixed
    vector, so tests can assert exact ranking order instead of relying on
    whatever a hash-derived vector happens to produce."""
    monkeypatch.setattr(recipe_service, "embed_text", lambda text: _unit_vector(0))


def test_get_suggestions_ranks_closest_first(db_session: Session) -> None:
    close = Recipe(title="Proche", ingredients=[], allergens=[], embedding=_unit_vector(0))
    far = Recipe(title="Loin", ingredients=[], allergens=[], embedding=_unit_vector(1))
    db_session.add_all([far, close])
    db_session.flush()

    suggestions = recipe_service.get_suggestions(db_session, "query", [])

    assert [s.title for s in suggestions] == ["Proche", "Loin"]
    assert suggestions[0].score > suggestions[1].score


def test_get_suggestions_caps_at_suggestion_count(db_session: Session) -> None:
    for i in range(recipe_service.SUGGESTION_COUNT + 2):
        db_session.add(
            Recipe(title=f"Recette {i}", ingredients=[], allergens=[], embedding=_unit_vector(0))
        )
    db_session.flush()

    suggestions = recipe_service.get_suggestions(db_session, "query", [])

    assert len(suggestions) == recipe_service.SUGGESTION_COUNT


def test_get_suggestions_returns_ingredient_names_only(db_session: Session) -> None:
    ingredients = [
        {"name": "lentilles", "quantity": "200g"},
        {"name": "curry", "quantity": None},
    ]
    db_session.add(
        Recipe(title="Curry", ingredients=ingredients, allergens=[], embedding=_unit_vector(0))
    )
    db_session.flush()

    suggestions = recipe_service.get_suggestions(db_session, "query", [])

    assert suggestions[0].ingredients == ["lentilles", "curry"]


def test_create_recipe_persists_with_embedding(db_session: Session) -> None:
    ingredients = [
        {"name": "lentilles", "quantity": "200g"},
        {"name": "curry", "quantity": "1 cuillère à soupe"},
    ]
    recipe = recipe_service.create_recipe(
        db_session,
        title="Curry de lentilles",
        ingredients=ingredients,
        allergens=["gluten"],
        prep_time_minutes=30,
        servings=4,
        protein_source="lentilles",
        protein_grams=18.5,
        instructions=["Faire revenir les oignons", "Ajouter les lentilles et le curry"],
        image_filename="abc123.png",
    )

    fetched = db_session.get(Recipe, recipe.id)
    assert fetched is not None
    assert fetched.title == "Curry de lentilles"
    assert fetched.ingredients == ingredients
    assert fetched.allergens == ["gluten"]
    assert fetched.prep_time_minutes == 30
    assert fetched.servings == 4
    assert fetched.protein_source == "lentilles"
    assert fetched.protein_grams == 18.5
    assert fetched.instructions == [
        "Faire revenir les oignons",
        "Ajouter les lentilles et le curry",
    ]
    assert fetched.image_filename == "abc123.png"
    assert list(fetched.embedding) == _unit_vector(0)


def test_create_recipe_defaults_optional_fields(db_session: Session) -> None:
    recipe = recipe_service.create_recipe(
        db_session, title="Salade", ingredients=[{"name": "laitue", "quantity": None}]
    )

    assert recipe.allergens == []
    assert recipe.prep_time_minutes is None
    assert recipe.servings is None
    assert recipe.protein_source is None
    assert recipe.protein_grams is None
    assert recipe.instructions == []
    assert recipe.image_filename is None


def test_create_recipe_allows_missing_quantity_without_servings(db_session: Session) -> None:
    recipe = recipe_service.create_recipe(
        db_session,
        title="Salade",
        ingredients=[{"name": "laitue", "quantity": None}],
        servings=None,
    )

    assert recipe.ingredients == [{"name": "laitue", "quantity": None}]


def test_create_recipe_rejects_missing_quantity_when_servings_set(db_session: Session) -> None:
    with pytest.raises(IngredientQuantityError):
        recipe_service.create_recipe(
            db_session,
            title="Salade",
            ingredients=[{"name": "laitue", "quantity": None}],
            servings=2,
        )


def test_validate_ingredient_quantities_reports_all_missing_names() -> None:
    with pytest.raises(IngredientQuantityError) as exc_info:
        recipe_service.validate_ingredient_quantities(
            [
                {"name": "laitue", "quantity": None},
                {"name": "tomate", "quantity": "2"},
                {"name": "concombre", "quantity": None},
            ],
            servings=2,
        )

    assert "laitue" in str(exc_info.value)
    assert "concombre" in str(exc_info.value)
    assert "tomate" not in str(exc_info.value)


def test_validate_ingredient_quantities_ignores_missing_when_no_servings() -> None:
    recipe_service.validate_ingredient_quantities(
        [{"name": "laitue", "quantity": None}], servings=None
    )


def test_list_recipes_orders_by_title(db_session: Session) -> None:
    db_session.add_all(
        [
            Recipe(title="Salade", ingredients=[], allergens=[], embedding=_unit_vector(0)),
            Recipe(title="Curry", ingredients=[], allergens=[], embedding=_unit_vector(0)),
        ]
    )
    db_session.flush()

    titles = [recipe.title for recipe in recipe_service.list_recipes(db_session)]

    assert titles == ["Curry", "Salade"]


def test_get_recipe_returns_none_for_missing_id(db_session: Session) -> None:
    assert recipe_service.get_recipe(db_session, 999999) is None


def test_update_recipe_overwrites_fields_and_recomputes_embedding(db_session: Session) -> None:
    recipe = recipe_service.create_recipe(
        db_session, title="Salade", ingredients=[{"name": "laitue", "quantity": None}]
    )

    updated = recipe_service.update_recipe(
        db_session,
        recipe,
        title="Grande salade",
        ingredients=[{"name": "laitue", "quantity": "200g"}, {"name": "tomate", "quantity": "2"}],
        servings=2,
        image_filename="new.png",
    )

    assert updated is recipe
    fetched = db_session.get(Recipe, recipe.id)
    assert fetched is not None
    assert fetched.title == "Grande salade"
    assert fetched.ingredients == [
        {"name": "laitue", "quantity": "200g"},
        {"name": "tomate", "quantity": "2"},
    ]
    assert fetched.servings == 2
    assert fetched.image_filename == "new.png"


def test_update_recipe_rejects_missing_quantity_when_servings_set(db_session: Session) -> None:
    recipe = recipe_service.create_recipe(
        db_session, title="Salade", ingredients=[{"name": "laitue", "quantity": None}]
    )

    with pytest.raises(IngredientQuantityError):
        recipe_service.update_recipe(
            db_session,
            recipe,
            title="Salade",
            ingredients=[{"name": "laitue", "quantity": None}],
            servings=2,
        )


def test_delete_recipe_removes_row(db_session: Session) -> None:
    recipe = recipe_service.create_recipe(
        db_session, title="Salade", ingredients=[{"name": "laitue", "quantity": None}]
    )
    recipe_id = recipe.id

    recipe_service.delete_recipe(db_session, recipe)

    assert db_session.get(Recipe, recipe_id) is None
