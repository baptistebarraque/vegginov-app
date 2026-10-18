"""Pure similarity primitives — no FastAPI or DB dependency.

This isolation is what lets a later phase swap in a multi-criteria score
without touching services or routes. cosine_similarity is the shared
primitive behind both the Title view (matching/embeddings.py vectors) and
the Ingredients view (matching/ingredient_similarity.py's FlavorGraph
vectors) — see matching/fusion.py for how the two views are combined.

Everything here is numpy-vectorized: the first implementation summed vectors
element by element in Python, which cost ~95% of a /suggestions request (see
docs/ARCHITECTURE.md "Vectorized matching"). normalize_rows lets callers
normalize once and then get every cosine of a batch from one matrix product.
"""

from collections.abc import Sequence

import numpy as np


def cosine_similarity(a: Sequence[float] | np.ndarray, b: Sequence[float] | np.ndarray) -> float:
    vector_a = np.asarray(a, dtype=np.float64)
    vector_b = np.asarray(b, dtype=np.float64)
    if vector_a.shape != vector_b.shape:
        raise ValueError("Vectors must have the same dimension")

    norm_a = np.linalg.norm(vector_a)
    norm_b = np.linalg.norm(vector_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(vector_a @ vector_b / (norm_a * norm_b))


def normalize_rows(matrix: np.ndarray) -> np.ndarray:
    """Scales every row of a 2-D array to unit length, so the dot product of
    two normalized rows is their cosine similarity. All-zero rows stay zero
    (cosine 0 with everything), matching cosine_similarity's zero-vector rule."""
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return np.divide(matrix, norms, out=np.zeros_like(matrix), where=norms != 0)
