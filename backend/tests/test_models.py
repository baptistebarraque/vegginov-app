from sqlalchemy.orm import Session

from veggie_app.models.recipe import EMBEDDING_DIM, Recipe
from veggie_app.models.user import User


def test_recipe_round_trip(db_session: Session) -> None:
    embedding = [0.1] * EMBEDDING_DIM
    recipe = Recipe(
        title="Curry de lentilles",
        ingredients=["lentilles", "lait de coco", "curry"],
        allergens=[],
        embedding=embedding,
    )
    db_session.add(recipe)
    db_session.flush()

    fetched = db_session.get(Recipe, recipe.id)

    assert fetched is not None
    assert fetched.title == "Curry de lentilles"
    assert fetched.ingredients == ["lentilles", "lait de coco", "curry"]
    assert fetched.prep_time_minutes is None
    assert fetched.created_at is not None
    assert list(fetched.embedding) == embedding


def test_user_round_trip(db_session: Session) -> None:
    user = User(email="admin@example.com")
    db_session.add(user)
    db_session.flush()

    fetched = db_session.get(User, user.id)

    assert fetched is not None
    assert fetched.email == "admin@example.com"
    assert fetched.created_at is not None
