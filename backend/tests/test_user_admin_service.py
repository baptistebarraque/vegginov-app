from sqlalchemy.orm import Session

from veggie_app.matching.embeddings import EMBEDDING_DIM
from veggie_app.models.recipe import Recipe
from veggie_app.models.user import User
from veggie_app.services import (
    auth_service,
    like_service,
    preference_service,
    user_admin_service,
    watchlist_service,
)


def _add_user(db_session: Session, email: str, *, is_admin: bool = False) -> User:
    user = auth_service.register_user(db_session, email, "password", is_admin=is_admin)
    db_session.flush()
    return user


def _add_recipe(db_session: Session, title: str = "Curry de lentilles") -> Recipe:
    recipe = Recipe(title=title, ingredients=[], allergens=[], embedding=[0.1] * EMBEDDING_DIM)
    db_session.add(recipe)
    db_session.flush()
    return recipe


def test_list_user_summaries_is_empty_without_accounts(db_session: Session) -> None:
    assert user_admin_service.list_user_summaries(db_session) == []


def test_list_user_summaries_returns_newest_account_first(db_session: Session) -> None:
    _add_user(db_session, "first@example.com")
    _add_user(db_session, "second@example.com")

    summaries = user_admin_service.list_user_summaries(db_session)

    assert [summary.user.email for summary in summaries] == [
        "second@example.com",
        "first@example.com",
    ]


def test_list_user_summaries_reports_zero_counts_for_a_fresh_account(
    db_session: Session,
) -> None:
    _add_user(db_session, "fresh@example.com")

    summary = user_admin_service.list_user_summaries(db_session)[0]

    assert summary.watchlist_count == 0
    assert summary.like_count == 0
    assert summary.has_preferences is False


def test_list_user_summaries_counts_watchlist_and_likes_per_user(
    db_session: Session,
) -> None:
    active = _add_user(db_session, "active@example.com")
    _add_user(db_session, "quiet@example.com")
    curry = _add_recipe(db_session, "Curry de lentilles")
    dahl = _add_recipe(db_session, "Dahl de pois cassés")
    watchlist_service.add(db_session, active.id, curry.id)
    watchlist_service.add(db_session, active.id, dahl.id)
    like_service.add(db_session, active.id, curry.id)

    summaries = {
        summary.user.email: summary
        for summary in user_admin_service.list_user_summaries(db_session)
    }

    assert summaries["active@example.com"].watchlist_count == 2
    assert summaries["active@example.com"].like_count == 1
    assert summaries["quiet@example.com"].watchlist_count == 0
    assert summaries["quiet@example.com"].like_count == 0


def test_list_user_summaries_flags_saved_preferences_and_admin_role(
    db_session: Session,
) -> None:
    admin = _add_user(db_session, "admin@example.com", is_admin=True)
    _add_user(db_session, "plain@example.com")
    preference_service.upsert_preferences(
        db_session,
        admin.id,
        calorie_orientation="low",
        diet="vegetarian",
        allergens=["gluten"],
        price_range=2,
    )

    summaries = {
        summary.user.email: summary
        for summary in user_admin_service.list_user_summaries(db_session)
    }

    assert summaries["admin@example.com"].has_preferences is True
    assert summaries["admin@example.com"].user.is_admin is True
    assert summaries["plain@example.com"].has_preferences is False
    assert summaries["plain@example.com"].user.is_admin is False


def test_get_user_detail_returns_none_for_an_unknown_id(db_session: Session) -> None:
    assert user_admin_service.get_user_detail(db_session, 999999) is None


def test_get_user_detail_without_preferences(db_session: Session) -> None:
    user = _add_user(db_session, "fresh@example.com")

    detail = user_admin_service.get_user_detail(db_session, user.id)

    assert detail is not None
    assert detail.preferences is None
    assert detail.summary.has_preferences is False
    assert detail.watchlist == []
    assert detail.likes == []


def test_get_user_detail_returns_preferences_watchlist_and_likes(
    db_session: Session,
) -> None:
    user = _add_user(db_session, "person@example.com")
    curry = _add_recipe(db_session, "Curry de lentilles")
    dahl = _add_recipe(db_session, "Dahl de pois cassés")
    preference_service.upsert_preferences(
        db_session,
        user.id,
        calorie_orientation="high",
        diet="vegan",
        allergens=["arachide"],
        price_range=1,
    )
    watchlist_service.add(db_session, user.id, curry.id)
    like_service.add(db_session, user.id, dahl.id)

    detail = user_admin_service.get_user_detail(db_session, user.id)

    assert detail is not None
    assert detail.preferences is not None
    assert detail.preferences.diet == "vegan"
    assert detail.preferences.allergens == ["arachide"]
    assert [recipe.title for _entry, recipe in detail.watchlist] == ["Curry de lentilles"]
    assert [recipe.title for _like, recipe in detail.likes] == ["Dahl de pois cassés"]
    assert detail.summary.watchlist_count == 1
    assert detail.summary.like_count == 1
