"""Business logic for reading/updating a user's preference profile."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from veggie_app.models.user_preference import UserPreference
from veggie_app.services.recipe_service import MAX_PRICE_TIER

CALORIE_ORIENTATIONS = ("low", "balanced", "high")
DIETS = ("omnivore", "vegetarian", "pescatarian", "vegan")


class CalorieOrientationError(ValueError):
    """Raised when calorie_orientation isn't one of CALORIE_ORIENTATIONS."""


class DietError(ValueError):
    """Raised when diet isn't one of DIETS."""


class PriceRangeError(ValueError):
    """Raised when price_range is outside the 1..MAX_PRICE_TIER range."""


def _validate(
    calorie_orientation: str | None, diet: str | None, price_range: int | None
) -> None:
    if calorie_orientation is not None and calorie_orientation not in CALORIE_ORIENTATIONS:
        raise CalorieOrientationError(
            f"orientation calorique inconnue : {calorie_orientation!r} "
            f"(valeurs autorisées : {', '.join(CALORIE_ORIENTATIONS)})"
        )
    if diet is not None and diet not in DIETS:
        raise DietError(f"régime inconnu : {diet!r} (valeurs autorisées : {', '.join(DIETS)})")
    if price_range is not None and not (1 <= price_range <= MAX_PRICE_TIER):
        raise PriceRangeError(f"price_range doit être compris entre 1 et {MAX_PRICE_TIER}")


def get_preferences(db: Session, user_id: int) -> UserPreference | None:
    return db.execute(
        select(UserPreference).where(UserPreference.user_id == user_id)
    ).scalar_one_or_none()


def upsert_preferences(
    db: Session,
    user_id: int,
    *,
    calorie_orientation: str | None,
    diet: str | None,
    allergens: list[str],
    price_range: int | None,
) -> UserPreference:
    _validate(calorie_orientation, diet, price_range)

    preferences = get_preferences(db, user_id)
    if preferences is None:
        preferences = UserPreference(user_id=user_id)
        db.add(preferences)

    preferences.calorie_orientation = calorie_orientation
    preferences.diet = diet
    preferences.allergens = allergens
    preferences.price_range = price_range
    db.flush()
    return preferences
