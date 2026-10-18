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

The score measures how well a candidate *covers the query*: each query
ingredient counts in proportion to its weight (IngredientWeights — rare
ingredients count more than garlic, salt or olive oil, which nearly every
recipe shares), and a query ingredient the candidate can't match counts as 0
rather than being left out. See docs/ARCHITECTURE.md "Ingredient weighting".
"""

import math
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from functools import lru_cache

import numpy as np
from scipy.optimize import linear_sum_assignment

from veggie_app.matching.flavorgraph import get_concept, get_vector
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


@dataclass(frozen=True)
class IngredientWeights:
    """How informative each ingredient is, from how many recipes of the corpus
    contain it: smoothed inverse document frequency, log((1 + N) / (1 + df)) + 1,
    counted per FlavorGraph concept so "oignon émincé" and "oignons" are one
    ingredient. Garlic (in half the recipes) weighs ~1.7, an ingredient in a
    single recipe ~5.7.

    An ingredient no recipe contains gets `unknown_weight` (the median weight
    of the corpus) instead of the maximum the formula would give: a frequency
    of zero is no evidence of how distinctive it is — it's typically another
    wording of something the corpus has ("bière brune" where recipes say
    "bière") — and since no candidate can match it exactly, a top weight would
    only dilute the ingredients that can."""

    document_frequencies: dict[str, int]
    recipe_count: int
    unknown_weight: float = 1.0

    def weight(self, ingredient: str) -> float:
        concept = get_concept(ingredient)
        frequency = self.document_frequencies.get(concept) if concept else None
        if frequency is None:
            return self.unknown_weight
        return _idf(frequency, self.recipe_count)


def _idf(frequency: int, recipe_count: int) -> float:
    return math.log((1 + recipe_count) / (1 + frequency)) + 1


UNIFORM_WEIGHTS = IngredientWeights(document_frequencies={}, recipe_count=0)


def compute_ingredient_weights(ingredient_lists: Iterable[Sequence[str]]) -> IngredientWeights:
    """Counts, for each FlavorGraph concept, the recipes containing it — once
    per recipe, however many times it is listed."""
    frequencies: Counter[str] = Counter()
    recipe_count = 0
    for ingredients in ingredient_lists:
        recipe_count += 1
        frequencies.update(
            {concept for concept in (get_concept(name) for name in ingredients) if concept}
        )
    corpus_weights = [_idf(frequency, recipe_count) for frequency in frequencies.values()]
    return IngredientWeights(
        document_frequencies=dict(frequencies),
        recipe_count=recipe_count,
        unknown_weight=float(np.median(corpus_weights)) if corpus_weights else 1.0,
    )


def ingredient_weight_vector(ingredients: Sequence[str], weights: IngredientWeights) -> np.ndarray:
    """The weight of each row of ingredient_matrix(ingredients), in the same
    order (unresolvable ingredients are dropped from both)."""
    return np.array(
        [weights.weight(name) for name in ingredients if _unit_vector(name) is not None],
        dtype=np.float64,
    )


def matrix_set_similarity(
    query_matrix: np.ndarray,
    candidate_matrix: np.ndarray,
    query_weights: np.ndarray | None = None,
) -> float:
    """How well the candidate's ingredients cover the query's, in [0, 1]:
    optimal one-to-one matching (Hungarian algorithm) that maximizes the
    weighted similarity, divided by the total weight of *all* query
    ingredients — so an unmatched query ingredient (the candidate has fewer
    ingredients) counts as 0 instead of being ignored. Rows are unit vectors,
    so one matrix product gives every pairwise cosine; negative cosines count
    as 0. Without weights every query ingredient counts the same. Returns 0.0
    if either side has no row — nothing left to compare."""
    if len(query_matrix) == 0 or len(candidate_matrix) == 0:
        return 0.0
    if query_weights is None:
        query_weights = np.ones(len(query_matrix))

    weighted = np.clip(query_matrix @ candidate_matrix.T, 0.0, None) * query_weights[:, None]
    row_indices, col_indices = linear_sum_assignment(weighted, maximize=True)
    return float(weighted[row_indices, col_indices].sum() / query_weights.sum())


def ingredient_set_similarity(ingredients_a: list[str], ingredients_b: list[str]) -> float:
    """Convenience wrapper over ingredient_matrix + matrix_set_similarity for
    a one-off comparison of two ingredient lists."""
    return matrix_set_similarity(ingredient_matrix(ingredients_a), ingredient_matrix(ingredients_b))
