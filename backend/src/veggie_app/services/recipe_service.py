"""Business logic for generating recipe suggestions."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from veggie_app.matching.embeddings import build_query_text, embed_text
from veggie_app.matching.similarity import rank_by_similarity
from veggie_app.models.recipe import Recipe
from veggie_app.schemas.recipe import RecipeSuggestion

SUGGESTION_COUNT = 4


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
            ingredients=recipes_by_id[recipe_id].ingredients,
            score=score,
        )
        for recipe_id, score in ranked
    ]
