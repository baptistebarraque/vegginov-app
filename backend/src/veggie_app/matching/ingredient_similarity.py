"""Non-protein ingredient-set similarity: FlavorGraph embeddings + the
Hungarian algorithm for optimal one-to-one matching between two recipes'
ingredient lists.

Protein ingredients (meat/fish and their vegetarian substitutes) are
deliberately handled elsewhere (matching/substitution.py's hand-curated
table) rather than here: FlavorGraph's embeddings capture "what gets cooked
together" (recipe co-occurrence), not "what plays the same role as", so they
aren't reliable for judging whether tofu is a good stand-in for chicken. This
module is for everything else — vegetables, aromatics, sauces, spices —
where co-occurrence is exactly the right signal. See docs design notes
section 3.1.

Vectors are precomputed and cached at two levels, so ranking N recipes
doesn't redo any of this work on every request: each ingredient name is
resolved and normalized once (_unit_vector), and each recipe's ingredient
list is stacked into a matrix once (ingredient_matrix). Scoring is split in
two so a caller ranking many recipes against one query builds the query's
matrix once and reuses it for every candidate (matrix_set_similarity). See
docs/ARCHITECTURE.md "Vectorized matching".
"""

from collections.abc import Sequence
from functools import lru_cache

import numpy as np
from scipy.optimize import linear_sum_assignment

from veggie_app.matching.flavorgraph import get_vector
from veggie_app.matching.similarity import normalize_rows

# FlavorGraph's vector size, used for the (0, dim) matrix of a list with no
# resolvable ingredient.
FLAVORGRAPH_DIM = 300

# Bounds the per-name cache. Only names in SOURCE_TO_FLAVORGRAPH (~570) can
# resolve to a vector; everything else caches as None, so even a full cache
# stays a few MB. The bound only matters for free-text query names.
_UNIT_VECTOR_CACHE_SIZE = 16384

# Bounds the per-ingredient-list cache: one entry per recipe in the corpus
# plus recent queries. An entry is ~1.2 KB per resolvable ingredient (300
# float32 values), so ~12 KB for a typical recipe — a few MB for today's
# corpus, ~100 MB at the bound. A corpus larger than the bound still ranks
# correctly; it just rebuilds the evicted matrices.
_INGREDIENT_MATRIX_CACHE_SIZE = 8192


@lru_cache(maxsize=_UNIT_VECTOR_CACHE_SIZE)
def _unit_vector(name: str) -> np.ndarray | None:
    """`name`'s FlavorGraph vector scaled to unit length (None if unmapped),
    computed once per name. Marked read-only because the same array is handed
    to every caller."""
    vector = get_vector(name)
    if vector is None:
        return None
    unit = normalize_rows(np.asarray(vector, dtype=np.float32).reshape(1, -1))[0]
    unit.flags.writeable = False
    return unit


@lru_cache(maxsize=_INGREDIENT_MATRIX_CACHE_SIZE)
def _stacked_unit_vectors(ingredients: tuple[str, ...]) -> np.ndarray:
    vectors = [v for v in (_unit_vector(name) for name in ingredients) if v is not None]
    matrix = np.stack(vectors) if vectors else np.empty((0, FLAVORGRAPH_DIM), dtype=np.float32)
    matrix.flags.writeable = False
    return matrix


def ingredient_matrix(ingredients: Sequence[str]) -> np.ndarray:
    """Stacks the unit vectors of every resolvable ingredient into a read-only
    (k, FLAVORGRAPH_DIM) matrix, one row per ingredient, cached per ingredient
    list. Ingredients with no FlavorGraph mapping are dropped (get_vector
    already logs the miss). Editing a recipe's ingredients changes the list,
    so a stale matrix is never served."""
    return _stacked_unit_vectors(tuple(ingredients))


def clear_vector_caches() -> None:
    """Empties both vector caches — for tests that swap get_vector out."""
    _unit_vector.cache_clear()
    _stacked_unit_vectors.cache_clear()


def matrix_set_similarity(matrix_a: np.ndarray, matrix_b: np.ndarray) -> float:
    """Optimal one-to-one matching (Hungarian algorithm) between two
    ingredient matrices from ingredient_matrix, averaged over matched pairs.
    Rows are unit vectors, so one matrix product gives every pairwise cosine.
    Returns 0.0 if either side has no row — nothing left to compare."""
    if len(matrix_a) == 0 or len(matrix_b) == 0:
        return 0.0

    similarities = matrix_a @ matrix_b.T
    row_indices, col_indices = linear_sum_assignment(similarities, maximize=True)
    # sum / count rather than .mean(): same value, a fraction of the call
    # overhead, which adds up at one call per candidate recipe.
    return float(similarities[row_indices, col_indices].sum()) / len(row_indices)


def ingredient_set_similarity(ingredients_a: list[str], ingredients_b: list[str]) -> float:
    """Convenience wrapper over ingredient_matrix + matrix_set_similarity for
    a one-off comparison of two ingredient lists."""
    return matrix_set_similarity(ingredient_matrix(ingredients_a), ingredient_matrix(ingredients_b))
