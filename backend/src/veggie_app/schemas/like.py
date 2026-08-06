"""Request/response models for the likes API. Validation only, no logic."""

from pydantic import BaseModel


class LikeStatusResponse(BaseModel):
    """Returned by POST/DELETE — the authoritative state after the toggle, so
    the frontend can set the exact count and liked flag rather than guessing."""

    recipe_id: int
    like_count: int
    is_liked: bool


class LikedRecipeResponse(BaseModel):
    recipe_id: int
    title: str
    image_url: str | None
    like_count: int


class LikesResponse(BaseModel):
    likes: list[LikedRecipeResponse]
