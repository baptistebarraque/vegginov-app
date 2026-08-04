"""Request/response models for the recipe APIs. Validation only, no logic."""

from pydantic import BaseModel, Field


class SuggestionRequest(BaseModel):
    title: str
    ingredients: list[str] = Field(default_factory=list)
    # When a session cookie is present, allergen exclusion from the user's
    # preferences is applied by default; set true to see everything anyway.
    ignore_preferences: bool = False


class IngredientEntrySchema(BaseModel):
    name: str
    quantity: str | None = None


class RecipeSuggestion(BaseModel):
    id: int
    title: str
    ingredients: list[IngredientEntrySchema]
    score: float
    allergens: list[str]
    prep_time_minutes: int | None
    servings: int | None
    protein_source: str | None
    protein_grams: float | None
    calories_per_portion: float | None
    price_tier: int | None
    protein_density: float | None  # grams of protein per 100 kcal, computed
    instructions: list[str]
    image_url: str | None
    is_watchlisted: bool  # false (never null) when the caller is anonymous


class SuggestionResponse(BaseModel):
    suggestions: list[RecipeSuggestion]


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
    calories_per_portion: float | None
    price_tier: int | None
    protein_density: float | None  # grams of protein per 100 kcal, computed
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
