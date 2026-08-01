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
from veggie_app.matching.similarity import cosine_similarity

DEFAULT_TITLE_WEIGHT = 0.3


@dataclass
class CandidateRecipe:
    id: int
    title_embedding: Sequence[float]
    ingredient_names: list[str]
    protein_source: str | None


def fuse_scores(
    title_score: float, ingredients_score: float, title_weight: float = DEFAULT_TITLE_WEIGHT
) -> float:
    return title_weight * title_score + (1 - title_weight) * ingredients_score


def rank_candidates(
    query_title_embedding: Sequence[float],
    query_ingredients: list[str],
    candidates: Sequence[CandidateRecipe],
    top_k: int = 4,
    title_weight: float = DEFAULT_TITLE_WEIGHT,
) -> list[tuple[int, float]]:
    """Returns (candidate_id, score) pairs, highest score first, truncated to
    top_k."""
    scored = [
        (
            candidate.id,
            fuse_scores(
                cosine_similarity(query_title_embedding, candidate.title_embedding),
                ingredients_view_score(
                    query_ingredients, candidate.ingredient_names, candidate.protein_source
                ),
                title_weight,
            ),
        )
        for candidate in candidates
    ]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:top_k]
