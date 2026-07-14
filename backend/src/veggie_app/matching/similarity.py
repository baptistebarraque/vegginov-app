"""Pure similarity-ranking logic — no FastAPI or DB dependency.

This isolation is what lets a later phase swap in a multi-criteria score
(e.g. embedding similarity + nutritional equivalence) without touching
services or routes.
"""

import math
from collections.abc import Sequence


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b):
        raise ValueError("Vectors must have the same dimension")

    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


def rank_by_similarity(
    query_embedding: Sequence[float],
    candidates: Sequence[tuple[int, Sequence[float]]],
    top_k: int = 4,
) -> list[tuple[int, float]]:
    """Returns (candidate_id, score) pairs, highest score first, truncated to top_k."""
    scored = [
        (candidate_id, cosine_similarity(query_embedding, embedding))
        for candidate_id, embedding in candidates
    ]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:top_k]
