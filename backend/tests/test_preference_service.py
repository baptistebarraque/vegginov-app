import pytest
from sqlalchemy.orm import Session

from veggie_app.services import auth_service, preference_service
from veggie_app.services.preference_service import (
    CalorieOrientationError,
    DietError,
    PriceRangeError,
)


def _make_user(db_session: Session):
    return auth_service.register_user(db_session, "person@example.com", "password")


def test_get_preferences_returns_none_before_any_upsert(db_session: Session) -> None:
    user = _make_user(db_session)

    assert preference_service.get_preferences(db_session, user.id) is None


def test_upsert_preferences_creates_a_row(db_session: Session) -> None:
    user = _make_user(db_session)

    preferences = preference_service.upsert_preferences(
        db_session,
        user.id,
        calorie_orientation="low",
        diet="vegan",
        allergens=["gluten", "lactose"],
        price_range=2,
    )

    assert preferences.calorie_orientation == "low"
    assert preferences.diet == "vegan"
    assert preferences.allergens == ["gluten", "lactose"]
    assert preferences.price_range == 2


def test_upsert_preferences_updates_the_same_row(db_session: Session) -> None:
    user = _make_user(db_session)
    preference_service.upsert_preferences(
        db_session,
        user.id,
        calorie_orientation="low",
        diet="vegan",
        allergens=["gluten"],
        price_range=1,
    )

    updated = preference_service.upsert_preferences(
        db_session,
        user.id,
        calorie_orientation="high",
        diet="omnivore",
        allergens=[],
        price_range=3,
    )

    fetched = preference_service.get_preferences(db_session, user.id)
    assert fetched is not None
    assert fetched.id == updated.id
    assert fetched.calorie_orientation == "high"
    assert fetched.allergens == []


def test_upsert_preferences_rejects_invalid_calorie_orientation(db_session: Session) -> None:
    user = _make_user(db_session)

    with pytest.raises(CalorieOrientationError):
        preference_service.upsert_preferences(
            db_session,
            user.id,
            calorie_orientation="not-a-real-value",
            diet=None,
            allergens=[],
            price_range=None,
        )


def test_upsert_preferences_rejects_invalid_diet(db_session: Session) -> None:
    user = _make_user(db_session)

    with pytest.raises(DietError):
        preference_service.upsert_preferences(
            db_session,
            user.id,
            calorie_orientation=None,
            diet="carnivore",
            allergens=[],
            price_range=None,
        )


def test_upsert_preferences_rejects_price_range_out_of_bounds(db_session: Session) -> None:
    user = _make_user(db_session)

    with pytest.raises(PriceRangeError):
        preference_service.upsert_preferences(
            db_session,
            user.id,
            calorie_orientation=None,
            diet=None,
            allergens=[],
            price_range=4,
        )
