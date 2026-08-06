from sqlalchemy.orm import Session

from veggie_app.matching.embeddings import EMBEDDING_DIM
from veggie_app.models.recipe import Recipe
from veggie_app.services import auth_service, like_service


def _make_user_and_recipe(db_session: Session):
    user = auth_service.register_user(db_session, "person@example.com", "password")
    recipe = Recipe(
        title="Curry de lentilles", ingredients=[], allergens=[], embedding=[0.1] * EMBEDDING_DIM
    )
    db_session.add(recipe)
    db_session.flush()
    return user, recipe


def test_add_creates_a_like(db_session: Session) -> None:
    user, recipe = _make_user_and_recipe(db_session)

    like = like_service.add(db_session, user.id, recipe.id)

    assert like.user_id == user.id
    assert like.recipe_id == recipe.id


def test_add_is_idempotent(db_session: Session) -> None:
    user, recipe = _make_user_and_recipe(db_session)

    first = like_service.add(db_session, user.id, recipe.id)
    second = like_service.add(db_session, user.id, recipe.id)

    assert first.id == second.id
    assert len(like_service.list_for_user(db_session, user.id)) == 1


def test_remove_deletes_the_like(db_session: Session) -> None:
    user, recipe = _make_user_and_recipe(db_session)
    like_service.add(db_session, user.id, recipe.id)

    like_service.remove(db_session, user.id, recipe.id)

    assert like_service.get_like(db_session, user.id, recipe.id) is None


def test_remove_is_idempotent_when_not_present(db_session: Session) -> None:
    user, recipe = _make_user_and_recipe(db_session)

    like_service.remove(db_session, user.id, recipe.id)  # should not raise


def test_list_for_user_orders_most_recent_first(db_session: Session) -> None:
    user = auth_service.register_user(db_session, "person@example.com", "password")
    first = Recipe(title="Premier", ingredients=[], allergens=[], embedding=[0.1] * EMBEDDING_DIM)
    second = Recipe(title="Second", ingredients=[], allergens=[], embedding=[0.1] * EMBEDDING_DIM)
    db_session.add_all([first, second])
    db_session.flush()
    like_service.add(db_session, user.id, first.id)
    like_service.add(db_session, user.id, second.id)

    likes = like_service.list_for_user(db_session, user.id)

    assert [recipe.title for _, recipe in likes] == ["Second", "Premier"]


def test_liked_recipe_ids_returns_only_this_users_likes(db_session: Session) -> None:
    user_a = auth_service.register_user(db_session, "a@example.com", "password")
    user_b = auth_service.register_user(db_session, "b@example.com", "password")
    recipe = Recipe(title="Curry", ingredients=[], allergens=[], embedding=[0.1] * EMBEDDING_DIM)
    db_session.add(recipe)
    db_session.flush()
    like_service.add(db_session, user_a.id, recipe.id)

    assert like_service.liked_recipe_ids(db_session, user_a.id) == {recipe.id}
    assert like_service.liked_recipe_ids(db_session, user_b.id) == set()


def test_like_counts_aggregates_across_users(db_session: Session) -> None:
    user_a = auth_service.register_user(db_session, "a@example.com", "password")
    user_b = auth_service.register_user(db_session, "b@example.com", "password")
    liked_twice = Recipe(title="Populaire", ingredients=[], allergens=[], embedding=[0.1] * EMBEDDING_DIM)
    liked_once = Recipe(title="Discrète", ingredients=[], allergens=[], embedding=[0.1] * EMBEDDING_DIM)
    liked_never = Recipe(title="Ignorée", ingredients=[], allergens=[], embedding=[0.1] * EMBEDDING_DIM)
    db_session.add_all([liked_twice, liked_once, liked_never])
    db_session.flush()
    like_service.add(db_session, user_a.id, liked_twice.id)
    like_service.add(db_session, user_b.id, liked_twice.id)
    like_service.add(db_session, user_a.id, liked_once.id)

    counts = like_service.like_counts(
        db_session, [liked_twice.id, liked_once.id, liked_never.id]
    )

    # Recipes with no likes are absent from the dict — callers use .get(id, 0).
    assert counts == {liked_twice.id: 2, liked_once.id: 1}


def test_like_counts_with_no_ids_returns_empty(db_session: Session) -> None:
    assert like_service.like_counts(db_session, []) == {}
