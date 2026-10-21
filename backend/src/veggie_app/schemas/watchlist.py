"""Request/response models for the watchlist API. Validation only, no logic."""

from datetime import date

from pydantic import BaseModel, Field


class WatchlistUpdateRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=2000)
    planned_for: date | None = None


class WatchlistEntryResponse(BaseModel):
    recipe_id: int
    title: str
    image_url: str | None
    notes: str | None
    planned_for: date | None


class WatchlistResponse(BaseModel):
    entries: list[WatchlistEntryResponse]
