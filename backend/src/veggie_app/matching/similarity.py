"""Pure similarity primitives — no FastAPI or DB dependency.

This isolation is what lets a later phase swap in a multi-criteria score
without touching services or routes. cosine_similarity is the shared
primitive behind both the Title view (matching/embeddings.py vectors) and
the Ingredients view (matching/ingredient_similarity.py's FlavorGraph
vectors) — see matching/fusion.py for how the two views are combined.
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
