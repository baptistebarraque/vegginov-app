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


class IngredientQuantityError(ValueError):
    """Raised when servings is set but at least one ingredient has no quantity."""


class ProteinSourceError(ValueError):
    """Raised when protein_source isn't one of RECIPE_PROTEIN_VOCABULARY."""


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


def list_protein_source_options() -> list[str]:
    return list(RECIPE_PROTEIN_VOCABULARY)


def _prepare_embedding(
    title: str,
    ingredients: list[IngredientEntry],
    servings: int | None,
    protein_source: str | None,
) -> list[float]:
    """Shared by create/update: validates quantities and protein_source, then
    embeds the recipe's title (the "Title view" — see matching/fusion.py).
    Ingredient-based similarity is handled separately, at query time, by
    matching/ingredients_view.py, so ingredient text is deliberately not
    folded into this embedding."""
    validate_ingredient_quantities(ingredients, servings)
    validate_protein_source(protein_source)
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
    instructions: list[str] | None = None,
    image_filename: str | None = None,
) -> Recipe:
    embedding = _prepare_embedding(title, ingredients, servings, protein_source)
    recipe = Recipe(
        title=title,
        ingredients=ingredients,
        allergens=allergens or [],
        prep_time_minutes=prep_time_minutes,
        servings=servings,
        protein_source=protein_source,
        protein_grams=protein_grams,
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
    instructions: list[str] | None = None,
    image_filename: str | None = None,
) -> Recipe:
    embedding = _prepare_embedding(title, ingredients, servings, protein_source)
    recipe.title = title
    recipe.ingredients = ingredients
    recipe.allergens = allergens or []
    recipe.prep_time_minutes = prep_time_minutes
    recipe.servings = servings
    recipe.protein_source = protein_source
    recipe.protein_grams = protein_grams
    recipe.instructions = instructions or []
    recipe.image_filename = image_filename
    recipe.embedding = embedding
    db.flush()
    return recipe


def delete_recipe(db: Session, recipe: Recipe) -> None:
    db.delete(recipe)
    db.flush()


def get_suggestions(db: Session, title: str, ingredients: list[str]) -> list[RecipeSuggestion]:
    query_title_embedding = embed_text(title)

    recipes = db.execute(select(Recipe)).scalars().all()
    candidates = [
        CandidateRecipe(
            id=recipe.id,
            title_embedding=recipe.embedding,
            ingredient_names=[ingredient["name"] for ingredient in recipe.ingredients],
            protein_source=recipe.protein_source,
        )
        for recipe in recipes
    ]
    ranked = rank_candidates(
        query_title_embedding, ingredients, candidates, top_k=SUGGESTION_COUNT
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
            instructions=recipes_by_id[recipe_id].instructions,
            image_url=image_service.image_url(recipes_by_id[recipe_id].image_filename),
        )
        for recipe_id, score in ranked
    ]
