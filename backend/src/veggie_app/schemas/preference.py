"""Request/response models for the preferences API. Validation only, no logic."""

from typing import Annotated

from pydantic import BaseModel, Field


class PreferenceRequest(BaseModel):
    # Size caps only; orientation, diet and price values are checked by
    # preference_service.
    calorie_orientation: str | None = Field(default=None, max_length=50)
    diet: str | None = Field(default=None, max_length=50)
    allergens: list[Annotated[str, Field(max_length=100)]] = Field(
        default_factory=list, max_length=50
    )
    price_range: int | None = None


class PreferenceResponse(BaseModel):
    calorie_orientation: str | None
    diet: str | None
    allergens: list[str]
    price_range: int | None
