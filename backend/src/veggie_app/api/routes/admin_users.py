"""GET /admin/users(/{user_id}) — admin-only, read-only view of every account.

Read-only by design: this surface exists so the admin can *see* who signed up
and what they saved, not to edit or delete accounts — account changes stay in
/auth/account, where they are the account owner's own action.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from veggie_app.database import get_db
from veggie_app.models.user import User
from veggie_app.schemas.admin_user import (
    AdminUserDetail,
    AdminUserListItem,
    AdminUserPreferences,
    AdminUserRecipeRef,
    AdminUserWatchlistItem,
)
from veggie_app.services import auth_service, image_service, user_admin_service
from veggie_app.services.user_admin_service import UserSummary

router = APIRouter(prefix="/admin/users")


def _to_list_item(summary: UserSummary) -> AdminUserListItem:
    return AdminUserListItem(
        id=summary.user.id,
        email=summary.user.email,
        is_admin=summary.user.is_admin,
        created_at=summary.user.created_at,
        watchlist_count=summary.watchlist_count,
        like_count=summary.like_count,
        has_preferences=summary.has_preferences,
    )


@router.get("", response_model=list[AdminUserListItem])
def list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(auth_service.require_admin),
) -> list[AdminUserListItem]:
    return [_to_list_item(summary) for summary in user_admin_service.list_user_summaries(db)]


@router.get("/{user_id}", response_model=AdminUserDetail)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(auth_service.require_admin),
) -> AdminUserDetail:
    detail = user_admin_service.get_user_detail(db, user_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    preferences = detail.preferences
    return AdminUserDetail(
        **_to_list_item(detail.summary).model_dump(),
        preferences=(
            None
            if preferences is None
            else AdminUserPreferences(
                calorie_orientation=preferences.calorie_orientation,
                diet=preferences.diet,
                allergens=preferences.allergens,
                price_range=preferences.price_range,
            )
        ),
        watchlist=[
            AdminUserWatchlistItem(
                recipe_id=recipe.id,
                title=recipe.title,
                image_url=image_service.image_url(recipe.image_filename),
                notes=entry.notes,
                planned_for=entry.planned_for,
            )
            for entry, recipe in detail.watchlist
        ],
        likes=[
            AdminUserRecipeRef(
                recipe_id=recipe.id,
                title=recipe.title,
                image_url=image_service.image_url(recipe.image_filename),
            )
            for _like, recipe in detail.likes
        ],
    )
