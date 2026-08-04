"""Request/response models for the preferences API. Validation only, no logic."""

from pydantic import BaseModel, Field


class PreferenceRequest(BaseModel):
    calorie_orientation: str | None = None
    diet: str | None = None
    allergens: list[str] = Field(default_factory=list)
    price_range: int | None = None


class PreferenceResponse(BaseModel):
    calorie_orientation: str | None
    diet: str | None
    allergens: list[str]
    price_range: int | None
