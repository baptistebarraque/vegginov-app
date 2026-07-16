"""Request/response models for the recipe APIs. Validation only, no logic."""

from pydantic import BaseModel, Field


class SuggestionRequest(BaseModel):
    title: str
    ingredients: list[str] = Field(default_factory=list)


class RecipeSuggestion(BaseModel):
    id: int
    title: str
    ingredients: list[str]
    score: float


class SuggestionResponse(BaseModel):
    suggestions: list[RecipeSuggestion]


class CreateRecipeRequest(BaseModel):
    title: str
    ingredients: list[str]
    allergens: list[str] = Field(default_factory=list)
    prep_time_minutes: int | None = None


class CreateRecipeResponse(BaseModel):
    id: int
    title: str
    ingredients: list[str]
    allergens: list[str]
    prep_time_minutes: int | None
