"""POST /suggestions — validate input, call the service, serialize output."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from veggie_app.database import get_db
from veggie_app.models.user import User
from veggie_app.schemas.recipe import SuggestionRequest, SuggestionResponse
from veggie_app.services import (
    auth_service,
    like_service,
    preference_service,
    recipe_service,
    watchlist_service,
)

router = APIRouter()


@router.post("/suggestions", response_model=SuggestionResponse)
def post_suggestions(
    request: SuggestionRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(auth_service.get_optional_user),
) -> SuggestionResponse:
    excluded_allergens = None
    max_price_tier = None
    calorie_orientation = None
    watchlisted_recipe_ids = None
    liked_recipe_ids = None
    if user is not None:
        if not request.ignore_preferences:
            preferences = preference_service.get_preferences(db, user.id)
            if preferences is not None:
                excluded_allergens = preferences.allergens
                max_price_tier = preferences.price_range
                calorie_orientation = preferences.calorie_orientation
        watchlisted_recipe_ids = watchlist_service.watchlisted_recipe_ids(db, user.id)
        liked_recipe_ids = like_service.liked_recipe_ids(db, user.id)

    suggestions = recipe_service.get_suggestions(
        db,
        request.title,
        request.ingredients,
        excluded_allergens,
        watchlisted_recipe_ids,
        max_price_tier,
        calorie_orientation,
        liked_recipe_ids=liked_recipe_ids,
    )
    return SuggestionResponse(suggestions=suggestions)
