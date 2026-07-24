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


class IngredientEntrySchema(BaseModel):
    name: str
    quantity: str | None = None


class RecipeResponse(BaseModel):
    """Shared by create/get/update — the full recipe detail shape."""

    id: int
    title: str
    ingredients: list[IngredientEntrySchema]
    allergens: list[str]
    prep_time_minutes: int | None
    servings: int | None
    protein_source: str | None
    protein_grams: float | None
    instructions: list[str]
    image_url: str | None


class RecipeListItem(BaseModel):
    id: int
    title: str
    image_url: str | None


class CsvImportRowError(BaseModel):
    row: int
    message: str


class CsvImportResponse(BaseModel):
    created_count: int
