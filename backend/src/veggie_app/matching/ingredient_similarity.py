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
"""

import numpy as np
from scipy.optimize import linear_sum_assignment

from veggie_app.matching.flavorgraph import get_vector
from veggie_app.matching.similarity import cosine_similarity


def ingredient_set_similarity(ingredients_a: list[str], ingredients_b: list[str]) -> float:
    """Optimal one-to-one matching (Hungarian algorithm) between two
    ingredient lists' FlavorGraph embeddings, averaged over matched pairs.
    Ingredients with no FlavorGraph mapping are dropped (get_vector already
    logs the miss). Returns 0.0 if either side has no resolvable ingredient
    at all — nothing left to compare."""
    vectors_a = [v for v in (get_vector(name) for name in ingredients_a) if v is not None]
    vectors_b = [v for v in (get_vector(name) for name in ingredients_b) if v is not None]

    if not vectors_a or not vectors_b:
        return 0.0

    cost_matrix = np.zeros((len(vectors_a), len(vectors_b)))
    for i, vector_a in enumerate(vectors_a):
        for j, vector_b in enumerate(vectors_b):
            cost_matrix[i, j] = 1 - cosine_similarity(vector_a, vector_b)

    row_indices, col_indices = linear_sum_assignment(cost_matrix)
    matched_similarities = [
        1 - cost_matrix[r, c] for r, c in zip(row_indices, col_indices, strict=True)
    ]
    return float(np.mean(matched_similarities))
