"""Business logic for recipe suggestions and admin recipe creation."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from veggie_app.matching.embeddings import embed_text
from veggie_app.matching.fusion import CandidateRecipe, rank_candidates
from veggie_app.matching.substitution import RECIPE_PROTEIN_VOCABULARY
from veggie_app.models.recipe import IngredientEntry, Recipe
from veggie_app.schemas.recipe import IngredientEntrySchema, RecipeSuggestion
from veggie_app.services import image_service

SUGGESTION_COUNT = 4

# Cost indicator scale: 1 (cheapest) .. MAX_PRICE_TIER (most expensive),
# rendered as € symbols in the UI.
MAX_PRICE_TIER = 3


class IngredientQuantityError(ValueError):
    """Raised when servings is set but at least one ingredient has no quantity."""


class ProteinSourceError(ValueError):
    """Raised when protein_source isn't one of RECIPE_PROTEIN_VOCABULARY."""


class PriceTierError(ValueError):
    """Raised when price_tier is outside the 1..MAX_PRICE_TIER range."""


def validate_ingredient_quantities(
    ingredients: list[IngredientEntry], servings: int | None
) -> None:
    """A recipe that states how many people it serves needs a quantity on
    every ingredient — otherwise "serves 4" is meaningless. Ingredients may
    omit quantity when servings is left blank."""
    if servings is None:
        return
    missing_names = [
        ingredient["name"] for ingredient in ingredients if not ingredient.get("quantity")
    ]
    if missing_names:
        raise IngredientQuantityError(
            "quantité obligatoire pour chaque ingrédient quand le nombre de personnes est "
            f"renseigné (manquant pour : {', '.join(missing_names)})"
        )


def validate_protein_source(protein_source: str | None) -> None:
    """protein_source is constrained to RECIPE_PROTEIN_VOCABULARY (rather than
    freeform text) so matching/substitution.py's table lookup — an exact
    match, no fuzzy matching — always finds the recipe's protein."""
    if protein_source is not None and protein_source not in RECIPE_PROTEIN_VOCABULARY:
        raise ProteinSourceError(
            f"source de protéines inconnue : {protein_source!r} "
            f"(valeurs autorisées : {', '.join(RECIPE_PROTEIN_VOCABULARY)})"
        )


def validate_price_tier(price_tier: int | None) -> None:
    """price_tier is a coarse cost indicator on a 1..MAX_PRICE_TIER scale
    (rendered as €/€€/€€€), not a currency amount."""
    if price_tier is not None and not (1 <= price_tier <= MAX_PRICE_TIER):
        raise PriceTierError(
            f"niveau de prix invalide : {price_tier!r} "
            f"(valeur attendue entre 1 et {MAX_PRICE_TIER})"
        )


def compute_protein_density(
    protein_grams: float | None, calories_per_portion: float | None
) -> float | None:
    """Protein density in grams of protein per 100 kcal — a derived read-only
    figure (never stored), so calories and protein stay the single source of
    truth. Returns None unless both inputs are present and calories are
    positive; rounded to one decimal."""
    if protein_grams is None or not calories_per_portion:
        return None
    return round(protein_grams / calories_per_portion * 100, 1)


def list_protein_source_options() -> list[str]:
    return list(RECIPE_PROTEIN_VOCABULARY)


def _prepare_embedding(
    title: str,
    ingredients: list[IngredientEntry],
    servings: int | None,
    protein_source: str | None,
    price_tier: int | None,
) -> list[float]:
    """Shared by create/update: validates the recipe's fields, then embeds its
    title (the "Title view" — see matching/fusion.py). Ingredient-based
    similarity is handled separately, at query time, by
    matching/ingredients_view.py, so ingredient text is deliberately not
    folded into this embedding."""
    validate_ingredient_quantities(ingredients, servings)
    validate_protein_source(protein_source)
    validate_price_tier(price_tier)
    return embed_text(title)


def create_recipe(
    db: Session,
    title: str,
    ingredients: list[IngredientEntry],
    allergens: list[str] | None = None,
    prep_time_minutes: int | None = None,
    servings: int | None = None,
    protein_source: str | None = None,
    protein_grams: float | None = None,
    calories_per_portion: float | None = None,
    price_tier: int | None = None,
    instructions: list[str] | None = None,
    image_filename: str | None = None,
) -> Recipe:
    embedding = _prepare_embedding(title, ingredients, servings, protein_source, price_tier)
    recipe = Recipe(
        title=title,
        ingredients=ingredients,
        allergens=allergens or [],
        prep_time_minutes=prep_time_minutes,
        servings=servings,
        protein_source=protein_source,
        protein_grams=protein_grams,
        calories_per_portion=calories_per_portion,
        price_tier=price_tier,
        instructions=instructions or [],
        image_filename=image_filename,
        embedding=embedding,
    )
    db.add(recipe)
    db.flush()
    return recipe


def list_recipes(db: Session) -> list[Recipe]:
    return list(db.execute(select(Recipe).order_by(Recipe.title)).scalars().all())


def get_recipe(db: Session, recipe_id: int) -> Recipe | None:
    return db.get(Recipe, recipe_id)


def update_recipe(
    db: Session,
    recipe: Recipe,
    title: str,
    ingredients: list[IngredientEntry],
    allergens: list[str] | None = None,
    prep_time_minutes: int | None = None,
    servings: int | None = None,
    protein_source: str | None = None,
    protein_grams: float | None = None,
    calories_per_portion: float | None = None,
    price_tier: int | None = None,
    instructions: list[str] | None = None,
    image_filename: str | None = None,
) -> Recipe:
    embedding = _prepare_embedding(title, ingredients, servings, protein_source, price_tier)
    recipe.title = title
    recipe.ingredients = ingredients
    recipe.allergens = allergens or []
    recipe.prep_time_minutes = prep_time_minutes
    recipe.servings = servings
    recipe.protein_source = protein_source
    recipe.protein_grams = protein_grams
    recipe.calories_per_portion = calories_per_portion
    recipe.price_tier = price_tier
    recipe.instructions = instructions or []
    recipe.image_filename = image_filename
    recipe.embedding = embedding
    db.flush()
    return recipe


def delete_recipe(db: Session, recipe: Recipe) -> None:
    db.delete(recipe)
    db.flush()


def get_suggestions(
    db: Session,
    title: str,
    ingredients: list[str],
    excluded_allergens: list[str] | None = None,
    watchlisted_recipe_ids: set[int] | None = None,
    max_price_tier: int | None = None,
    calorie_orientation: str | None = None,
) -> list[RecipeSuggestion]:
    query_title_embedding = embed_text(title)

    recipes = db.execute(select(Recipe)).scalars().all()
    if excluded_allergens:
        # Hard exclusion, applied before ranking — a declared allergen never
        # just soft-ranks a recipe lower (docs/ROADMAP.md Phase 4 preferences).
        excluded = set(excluded_allergens)
        recipes = [recipe for recipe in recipes if not excluded.intersection(recipe.allergens)]

    if max_price_tier is not None and max_price_tier < MAX_PRICE_TIER:
        # Hard budget cap, applied before ranking like the allergen filter. A
        # recipe priced above the user's budget is excluded outright; the top
        # tier (MAX_PRICE_TIER) means "indifferent" — every recipe fits — so we
        # skip the pass entirely there. Recipes with no price_tier yet (data not
        # populated) are kept, not dropped, so results don't collapse while the
        # CIQUAL/price backfill is still in progress.
        recipes = [
            recipe
            for recipe in recipes
            if recipe.price_tier is None or recipe.price_tier <= max_price_tier
        ]

    candidates = [
        CandidateRecipe(
            id=recipe.id,
            title_embedding=recipe.embedding,
            ingredient_names=[ingredient["name"] for ingredient in recipe.ingredients],
            protein_source=recipe.protein_source,
            calories_per_portion=recipe.calories_per_portion,
        )
        for recipe in recipes
    ]
    ranked = rank_candidates(
        query_title_embedding,
        ingredients,
        candidates,
        top_k=SUGGESTION_COUNT,
        calorie_orientation=calorie_orientation,
    )

    recipes_by_id = {recipe.id: recipe for recipe in recipes}
    return [
        RecipeSuggestion(
            id=recipe_id,
            title=recipes_by_id[recipe_id].title,
            ingredients=[
                IngredientEntrySchema(name=ingredient["name"], quantity=ingredient["quantity"])
                for ingredient in recipes_by_id[recipe_id].ingredients
            ],
            score=score,
            allergens=recipes_by_id[recipe_id].allergens,
            prep_time_minutes=recipes_by_id[recipe_id].prep_time_minutes,
            servings=recipes_by_id[recipe_id].servings,
            protein_source=recipes_by_id[recipe_id].protein_source,
            protein_grams=recipes_by_id[recipe_id].protein_grams,
            calories_per_portion=recipes_by_id[recipe_id].calories_per_portion,
            price_tier=recipes_by_id[recipe_id].price_tier,
            protein_density=compute_protein_density(
                recipes_by_id[recipe_id].protein_grams,
                recipes_by_id[recipe_id].calories_per_portion,
            ),
            instructions=recipes_by_id[recipe_id].instructions,
            image_url=image_service.image_url(recipes_by_id[recipe_id].image_filename),
            is_watchlisted=bool(watchlisted_recipe_ids) and recipe_id in watchlisted_recipe_ids,
        )
        for recipe_id, score in ranked
    ]
