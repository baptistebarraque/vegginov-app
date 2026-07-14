"""POST /suggestions — validate input, call the service, serialize output."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from veggie_app.database import get_db
from veggie_app.schemas.recipe import SuggestionRequest, SuggestionResponse
from veggie_app.services import recipe_service

router = APIRouter()


@router.post("/suggestions", response_model=SuggestionResponse)
def post_suggestions(
    request: SuggestionRequest, db: Session = Depends(get_db)
) -> SuggestionResponse:
    suggestions = recipe_service.get_suggestions(db, request.title, request.ingredients)
    return SuggestionResponse(suggestions=suggestions)
