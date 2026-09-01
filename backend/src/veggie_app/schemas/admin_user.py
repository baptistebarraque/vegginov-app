"""Request/response models for the admin users API. Validation only, no logic."""

from datetime import date, datetime

from pydantic import BaseModel


class AdminUserListItem(BaseModel):
    id: int
    email: str
    is_admin: bool
    created_at: datetime
    watchlist_count: int
    like_count: int
    has_preferences: bool


class AdminUserPreferences(BaseModel):
    calorie_orientation: str | None
    diet: str | None
    allergens: list[str]
    price_range: int | None


class AdminUserRecipeRef(BaseModel):
    recipe_id: int
    title: str
    image_url: str | None


class AdminUserWatchlistItem(AdminUserRecipeRef):
    notes: str | None
    planned_for: date | None


class AdminUserDetail(AdminUserListItem):
    # None when the user never saved a preference profile — preferences are
    # created lazily on the first PUT /preferences, so "no row" is a normal
    # state, not missing data.
    preferences: AdminUserPreferences | None
    watchlist: list[AdminUserWatchlistItem]
    likes: list[AdminUserRecipeRef]
