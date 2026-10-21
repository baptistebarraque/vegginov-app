"""Request/response models for the recipe APIs. Validation only, no logic."""

from typing import Annotated

from pydantic import BaseModel, Field

# Size caps on the public, unauthenticated query: far above any real recipe,
# low enough that a single request can't make the matching do unbounded work.
MAX_QUERY_TITLE_LENGTH = 200
MAX_QUERY_INGREDIENTS = 60
MAX_QUERY_INGREDIENT_LENGTH = 200


class SuggestionRequest(BaseModel):
    title: str = Field(max_length=MAX_QUERY_TITLE_LENGTH)
    ingredients: list[Annotated[str, Field(max_length=MAX_QUERY_INGREDIENT_LENGTH)]] = Field(
        default_factory=list, max_length=MAX_QUERY_INGREDIENTS
    )
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
    is_liked: bool  # false (never null) when the caller is anonymous
    like_count: int  # public total across all users; 0 when no one has liked it


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
    dish_types: list[str]
    cuisine: str | None


class DishStructureOptions(BaseModel):
    dish_types: list[str]
    cuisines: list[str]


class RecipeListItem(BaseModel):
    id: int
    title: str
    image_url: str | None


class CsvImportRowError(BaseModel):
    row: int
    message: str


class CsvImportResponse(BaseModel):
    created_count: int
