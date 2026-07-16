import pytest
from sqlalchemy.orm import Session

from veggie_app.matching.embeddings import EMBEDDING_DIM
from veggie_app.models.recipe import Recipe
from veggie_app.services import recipe_service


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


def test_create_recipe_persists_with_embedding(db_session: Session) -> None:
    recipe = recipe_service.create_recipe(
        db_session,
        title="Curry de lentilles",
        ingredients=["lentilles", "curry"],
        allergens=["gluten"],
        prep_time_minutes=30,
    )

    fetched = db_session.get(Recipe, recipe.id)
    assert fetched is not None
    assert fetched.title == "Curry de lentilles"
    assert fetched.ingredients == ["lentilles", "curry"]
    assert fetched.allergens == ["gluten"]
    assert fetched.prep_time_minutes == 30
    assert list(fetched.embedding) == _unit_vector(0)


def test_create_recipe_defaults_allergens_to_empty_list(db_session: Session) -> None:
    recipe = recipe_service.create_recipe(db_session, title="Salade", ingredients=["laitue"])

    assert recipe.allergens == []
    assert recipe.prep_time_minutes is None
