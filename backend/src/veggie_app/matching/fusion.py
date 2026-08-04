"""Fuses the Title view (matching/embeddings.py) and Ingredients view
(matching/ingredients_view.py) into the final ranking score (see docs design
notes, section 2). Fixed weights for now — DEFAULT_TITLE_WEIGHT is an
arbitrary starting point, same as ingredients_view.DEFAULT_PROTEIN_WEIGHT,
meant to be replaced by a small learned model once a set of manually judged
pairs exists.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from veggie_app.matching.ingredients_view import ingredients_view_score
from veggie_app.matching.nutrition_view import calorie_orientation_score
from veggie_app.matching.similarity import cosine_similarity

DEFAULT_TITLE_WEIGHT = 0.3

# How much the calorie-orientation match (matching/nutrition_view.py) pulls on
# the final score, blended on top of the title+ingredients similarity. Kept
# small on purpose: calorie orientation is a soft preference nudge, so taste
# similarity stays dominant and it mostly breaks ties.
CALORIE_WEIGHT = 0.15


@dataclass
class CandidateRecipe:
    id: int
    title_embedding: Sequence[float]
    ingredient_names: list[str]
    protein_source: str | None
    calories_per_portion: float | None = None


def fuse_scores(
    title_score: float, ingredients_score: float, title_weight: float = DEFAULT_TITLE_WEIGHT
) -> float:
    return title_weight * title_score + (1 - title_weight) * ingredients_score


def apply_calorie_orientation(
    similarity: float,
    calories_per_portion: float | None,
    calorie_orientation: str | None,
    calorie_weight: float = CALORIE_WEIGHT,
) -> float:
    """Blends the calorie-orientation match into a recipe's similarity score.
    When no orientation is requested the similarity is returned untouched, so
    anonymous users (and users indifferent to calories) get exactly the same
    ranking and scores as before this term existed."""
    if calorie_orientation is None:
        return similarity
    calorie_score = calorie_orientation_score(calories_per_portion, calorie_orientation)
    return (1 - calorie_weight) * similarity + calorie_weight * calorie_score


def rank_candidates(
    query_title_embedding: Sequence[float],
    query_ingredients: list[str],
    candidates: Sequence[CandidateRecipe],
    top_k: int = 4,
    title_weight: float = DEFAULT_TITLE_WEIGHT,
    calorie_orientation: str | None = None,
) -> list[tuple[int, float]]:
    """Returns (candidate_id, score) pairs, highest score first, truncated to
    top_k. When calorie_orientation is set, each recipe's similarity is nudged
    by how well its per-portion calories match that orientation."""
    scored = [
        (
            candidate.id,
            apply_calorie_orientation(
                fuse_scores(
                    cosine_similarity(query_title_embedding, candidate.title_embedding),
                    ingredients_view_score(
                        query_ingredients, candidate.ingredient_names, candidate.protein_source
                    ),
                    title_weight,
                ),
                candidate.calories_per_portion,
                calorie_orientation,
            ),
        )
        for candidate in candidates
    ]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:top_k]
