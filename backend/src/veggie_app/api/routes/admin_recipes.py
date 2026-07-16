"""POST /admin/recipes — admin-only, validate input, call the service, serialize output."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from veggie_app.database import get_db
from veggie_app.models.user import User
from veggie_app.schemas.recipe import CreateRecipeRequest, CreateRecipeResponse
from veggie_app.services import auth_service, recipe_service

router = APIRouter(prefix="/admin")


@router.post("/recipes", response_model=CreateRecipeResponse)
def create_recipe(
    request: CreateRecipeRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(auth_service.require_admin),
) -> CreateRecipeResponse:
    recipe = recipe_service.create_recipe(
        db,
        title=request.title,
        ingredients=request.ingredients,
        allergens=request.allergens,
        prep_time_minutes=request.prep_time_minutes,
    )
    db.commit()
    return CreateRecipeResponse(
        id=recipe.id,
        title=recipe.title,
        ingredients=recipe.ingredients,
        allergens=recipe.allergens,
        prep_time_minutes=recipe.prep_time_minutes,
    )
