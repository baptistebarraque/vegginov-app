"""Request/response models for the suggestions API. Validation only, no logic."""

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
