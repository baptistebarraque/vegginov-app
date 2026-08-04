from datetime import date

from sqlalchemy.orm import Session

from veggie_app.matching.embeddings import EMBEDDING_DIM
from veggie_app.models.recipe import Recipe
from veggie_app.services import auth_service, watchlist_service


def _make_user_and_recipe(db_session: Session):
    user = auth_service.register_user(db_session, "person@example.com", "password")
    recipe = Recipe(
        title="Curry de lentilles", ingredients=[], allergens=[], embedding=[0.1] * EMBEDDING_DIM
    )
    db_session.add(recipe)
    db_session.flush()
    return user, recipe


def test_add_creates_an_entry(db_session: Session) -> None:
    user, recipe = _make_user_and_recipe(db_session)

    entry = watchlist_service.add(db_session, user.id, recipe.id)

    assert entry.user_id == user.id
    assert entry.recipe_id == recipe.id
    assert entry.notes is None
    assert entry.planned_for is None


def test_add_is_idempotent(db_session: Session) -> None:
    user, recipe = _make_user_and_recipe(db_session)

    first = watchlist_service.add(db_session, user.id, recipe.id)
    second = watchlist_service.add(db_session, user.id, recipe.id)

    assert first.id == second.id
    assert len(watchlist_service.list_for_user(db_session, user.id)) == 1


def test_remove_deletes_the_entry(db_session: Session) -> None:
    user, recipe = _make_user_and_recipe(db_session)
    watchlist_service.add(db_session, user.id, recipe.id)

    watchlist_service.remove(db_session, user.id, recipe.id)

    assert watchlist_service.get_entry(db_session, user.id, recipe.id) is None


def test_remove_is_idempotent_when_not_present(db_session: Session) -> None:
    user, recipe = _make_user_and_recipe(db_session)

    watchlist_service.remove(db_session, user.id, recipe.id)  # should not raise


def test_update_entry_sets_notes_and_planned_for(db_session: Session) -> None:
    user, recipe = _make_user_and_recipe(db_session)
    watchlist_service.add(db_session, user.id, recipe.id)

    updated = watchlist_service.update_entry(
        db_session,
        user.id,
        recipe.id,
        notes="Pour dimanche soir",
        planned_for=date(2026, 8, 9),
    )

    assert updated is not None
    assert updated.notes == "Pour dimanche soir"
    assert updated.planned_for == date(2026, 8, 9)


def test_update_entry_returns_none_when_not_watchlisted(db_session: Session) -> None:
    user, recipe = _make_user_and_recipe(db_session)

    result = watchlist_service.update_entry(
        db_session, user.id, recipe.id, notes="x", planned_for=None
    )

    assert result is None


def test_list_for_user_orders_most_recent_first(db_session: Session) -> None:
    user = auth_service.register_user(db_session, "person@example.com", "password")
    first = Recipe(title="Premier", ingredients=[], allergens=[], embedding=[0.1] * EMBEDDING_DIM)
    second = Recipe(title="Second", ingredients=[], allergens=[], embedding=[0.1] * EMBEDDING_DIM)
    db_session.add_all([first, second])
    db_session.flush()
    watchlist_service.add(db_session, user.id, first.id)
    watchlist_service.add(db_session, user.id, second.id)

    entries = watchlist_service.list_for_user(db_session, user.id)

    assert [recipe.title for _, recipe in entries] == ["Second", "Premier"]


def test_watchlisted_recipe_ids_returns_only_this_users_entries(db_session: Session) -> None:
    user_a = auth_service.register_user(db_session, "a@example.com", "password")
    user_b = auth_service.register_user(db_session, "b@example.com", "password")
    recipe = Recipe(title="Curry", ingredients=[], allergens=[], embedding=[0.1] * EMBEDDING_DIM)
    db_session.add(recipe)
    db_session.flush()
    watchlist_service.add(db_session, user_a.id, recipe.id)

    assert watchlist_service.watchlisted_recipe_ids(db_session, user_a.id) == {recipe.id}
    assert watchlist_service.watchlisted_recipe_ids(db_session, user_b.id) == set()
