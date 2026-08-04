"""GET/PUT /preferences — validate input, call the service, serialize output.

Both routes require a logged-in user (any role) — preferences are a
per-account concern, not an admin one.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from veggie_app.database import get_db
from veggie_app.models.user import User
from veggie_app.models.user_preference import UserPreference
from veggie_app.schemas.preference import PreferenceRequest, PreferenceResponse
from veggie_app.services import auth_service, preference_service
from veggie_app.services.preference_service import (
    CalorieOrientationError,
    DietError,
    PriceRangeError,
)

router = APIRouter(prefix="/preferences")


def _to_response(preferences: UserPreference | None) -> PreferenceResponse:
    if preferences is None:
        return PreferenceResponse(
            calorie_orientation=None, diet=None, allergens=[], price_range=None
        )
    return PreferenceResponse(
        calorie_orientation=preferences.calorie_orientation,
        diet=preferences.diet,
        allergens=preferences.allergens,
        price_range=preferences.price_range,
    )


@router.get("", response_model=PreferenceResponse)
def get_preferences(
    user: User = Depends(auth_service.require_user), db: Session = Depends(get_db)
) -> PreferenceResponse:
    return _to_response(preference_service.get_preferences(db, user.id))


@router.put("", response_model=PreferenceResponse)
def update_preferences(
    request: PreferenceRequest,
    user: User = Depends(auth_service.require_user),
    db: Session = Depends(get_db),
) -> PreferenceResponse:
    try:
        preferences = preference_service.upsert_preferences(
            db,
            user.id,
            calorie_orientation=request.calorie_orientation,
            diet=request.diet,
            allergens=request.allergens,
            price_range=request.price_range,
        )
    except (CalorieOrientationError, DietError, PriceRangeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.commit()
    return _to_response(preferences)
