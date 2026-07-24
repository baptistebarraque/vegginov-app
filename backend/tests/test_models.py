from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from veggie_app.models.admin_session import AdminSession
from veggie_app.models.recipe import EMBEDDING_DIM, Recipe
from veggie_app.models.user import User


def test_recipe_round_trip(db_session: Session) -> None:
    embedding = [0.1] * EMBEDDING_DIM
    ingredients = [
        {"name": "lentilles", "quantity": "200g"},
        {"name": "lait de coco", "quantity": None},
        {"name": "curry", "quantity": None},
    ]
    recipe = Recipe(
        title="Curry de lentilles",
        ingredients=ingredients,
        allergens=[],
        embedding=embedding,
    )
    db_session.add(recipe)
    db_session.flush()

    fetched = db_session.get(Recipe, recipe.id)

    assert fetched is not None
    assert fetched.title == "Curry de lentilles"
    assert fetched.ingredients == ingredients
    assert fetched.prep_time_minutes is None
    assert fetched.created_at is not None
    assert list(fetched.embedding) == embedding


def test_user_round_trip(db_session: Session) -> None:
    user = User(email="admin@example.com", password_hash="hashed-password")
    db_session.add(user)
    db_session.flush()

    fetched = db_session.get(User, user.id)

    assert fetched is not None
    assert fetched.email == "admin@example.com"
    assert fetched.password_hash == "hashed-password"
    assert fetched.is_admin is False
    assert fetched.created_at is not None


def test_admin_session_round_trip(db_session: Session) -> None:
    user = User(email="admin@example.com", password_hash="hashed-password", is_admin=True)
    db_session.add(user)
    db_session.flush()

    expires_at = datetime.now(UTC) + timedelta(days=7)
    session = AdminSession(user_id=user.id, token_hash="a" * 64, expires_at=expires_at)
    db_session.add(session)
    db_session.flush()

    fetched = db_session.get(AdminSession, session.id)

    assert fetched is not None
    assert fetched.user_id == user.id
    assert fetched.token_hash == "a" * 64
    assert fetched.expires_at == expires_at
    assert fetched.created_at is not None
