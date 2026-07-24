"""Business logic for recipe suggestions and admin recipe creation."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from veggie_app.matching.embeddings import build_query_text, embed_text
from veggie_app.matching.similarity import rank_by_similarity
from veggie_app.models.recipe import IngredientEntry, Recipe
from veggie_app.schemas.recipe import RecipeSuggestion

SUGGESTION_COUNT = 4


class IngredientQuantityError(ValueError):
    """Raised when servings is set but at least one ingredient has no quantity."""


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


def _prepare_embedding(
    title: str, ingredients: list[IngredientEntry], servings: int | None
) -> list[float]:
    """Shared by create/update: validates quantities, then embeds the
    recipe from its title + ingredient names (quantities aren't semantically
    meaningful for similarity matching, so they're left out)."""
    validate_ingredient_quantities(ingredients, servings)
    ingredient_names = [ingredient["name"] for ingredient in ingredients]
    return embed_text(build_query_text(title, ingredient_names))


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
    embedding = _prepare_embedding(title, ingredients, servings)
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
    embedding = _prepare_embedding(title, ingredients, servings)
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
    query_embedding = embed_text(build_query_text(title, ingredients))

    recipes = db.execute(select(Recipe)).scalars().all()
    candidates = [(recipe.id, recipe.embedding) for recipe in recipes]
    ranked = rank_by_similarity(query_embedding, candidates, top_k=SUGGESTION_COUNT)

    recipes_by_id = {recipe.id: recipe for recipe in recipes}
    return [
        RecipeSuggestion(
            id=recipe_id,
            title=recipes_by_id[recipe_id].title,
            ingredients=[
                ingredient["name"] for ingredient in recipes_by_id[recipe_id].ingredients
            ],
            score=score,
        )
        for recipe_id, score in ranked
    ]
