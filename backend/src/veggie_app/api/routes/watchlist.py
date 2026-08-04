"""GET/POST/PATCH/DELETE /watchlist(/{recipe_id}) — validate input, call the
service, serialize output. All routes require a logged-in user (any role) —
the watchlist is a per-account concern, not an admin one.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from veggie_app.database import get_db
from veggie_app.models.recipe import Recipe
from veggie_app.models.user import User
from veggie_app.schemas.watchlist import (
    WatchlistEntryResponse,
    WatchlistResponse,
    WatchlistUpdateRequest,
)
from veggie_app.services import auth_service, image_service, recipe_service, watchlist_service

router = APIRouter(prefix="/watchlist")


def _get_recipe_or_404(db: Session, recipe_id: int) -> Recipe:
    recipe = recipe_service.get_recipe(db, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recette introuvable.")
    return recipe


@router.get("", response_model=WatchlistResponse)
def list_watchlist(
    user: User = Depends(auth_service.require_user), db: Session = Depends(get_db)
) -> WatchlistResponse:
    entries = watchlist_service.list_for_user(db, user.id)
    return WatchlistResponse(
        entries=[
            WatchlistEntryResponse(
                recipe_id=recipe.id,
                title=recipe.title,
                image_url=image_service.image_url(recipe.image_filename),
                notes=entry.notes,
                planned_for=entry.planned_for,
            )
            for entry, recipe in entries
        ]
    )


@router.post("/{recipe_id}", response_model=WatchlistEntryResponse)
def add_to_watchlist(
    recipe_id: int,
    user: User = Depends(auth_service.require_user),
    db: Session = Depends(get_db),
) -> WatchlistEntryResponse:
    recipe = _get_recipe_or_404(db, recipe_id)
    entry = watchlist_service.add(db, user.id, recipe_id)
    db.commit()
    return WatchlistEntryResponse(
        recipe_id=recipe.id,
        title=recipe.title,
        image_url=image_service.image_url(recipe.image_filename),
        notes=entry.notes,
        planned_for=entry.planned_for,
    )


@router.patch("/{recipe_id}", response_model=WatchlistEntryResponse)
def update_watchlist_entry(
    recipe_id: int,
    request: WatchlistUpdateRequest,
    user: User = Depends(auth_service.require_user),
    db: Session = Depends(get_db),
) -> WatchlistEntryResponse:
    recipe = _get_recipe_or_404(db, recipe_id)
    entry = watchlist_service.update_entry(
        db, user.id, recipe_id, notes=request.notes, planned_for=request.planned_for
    )
    if entry is None:
        raise HTTPException(status_code=404, detail="Cette recette n'est pas dans votre liste.")
    db.commit()
    return WatchlistEntryResponse(
        recipe_id=recipe.id,
        title=recipe.title,
        image_url=image_service.image_url(recipe.image_filename),
        notes=entry.notes,
        planned_for=entry.planned_for,
    )


@router.delete("/{recipe_id}", status_code=204)
def remove_from_watchlist(
    recipe_id: int,
    user: User = Depends(auth_service.require_user),
    db: Session = Depends(get_db),
) -> None:
    watchlist_service.remove(db, user.id, recipe_id)
    db.commit()
