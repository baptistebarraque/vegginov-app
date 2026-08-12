"""GET /likes and POST/DELETE /likes/{recipe_id} — validate input, call the
service, serialize output. All routes require a logged-in user: liking is a
per-account action. The *count* is public, but it rides on the /suggestions
response (see recipe_service.get_suggestions), not on these endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from veggie_app.database import get_db
from veggie_app.models.recipe import Recipe
from veggie_app.models.user import User
from veggie_app.schemas.like import LikedRecipeResponse, LikesResponse, LikeStatusResponse
from veggie_app.services import auth_service, image_service, like_service, recipe_service

router = APIRouter(prefix="/likes")


def _get_recipe_or_404(db: Session, recipe_id: int) -> Recipe:
    recipe = recipe_service.get_recipe(db, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recette introuvable.")
    return recipe


def _status(db: Session, recipe_id: int, *, is_liked: bool) -> LikeStatusResponse:
    like_count = like_service.like_counts(db, [recipe_id]).get(recipe_id, 0)
    return LikeStatusResponse(recipe_id=recipe_id, like_count=like_count, is_liked=is_liked)


@router.get("", response_model=LikesResponse)
def list_likes(
    user: User = Depends(auth_service.require_user), db: Session = Depends(get_db)
) -> LikesResponse:
    likes = like_service.list_for_user(db, user.id)
    counts = like_service.like_counts(db, [recipe.id for _, recipe in likes])
    return LikesResponse(
        likes=[
            LikedRecipeResponse(
                recipe_id=recipe.id,
                title=recipe.title,
                image_url=image_service.image_url(recipe.image_filename),
                like_count=counts.get(recipe.id, 0),
            )
            for _, recipe in likes
        ]
    )


@router.post("/{recipe_id}", response_model=LikeStatusResponse)
def like_recipe(
    recipe_id: int,
    user: User = Depends(auth_service.require_user),
    db: Session = Depends(get_db),
) -> LikeStatusResponse:
    _get_recipe_or_404(db, recipe_id)
    like_service.add(db, user.id, recipe_id)
    db.commit()
    return _status(db, recipe_id, is_liked=True)


@router.delete("/{recipe_id}", response_model=LikeStatusResponse)
def unlike_recipe(
    recipe_id: int,
    user: User = Depends(auth_service.require_user),
    db: Session = Depends(get_db),
) -> LikeStatusResponse:
    like_service.remove(db, user.id, recipe_id)
    db.commit()
    return _status(db, recipe_id, is_liked=False)
