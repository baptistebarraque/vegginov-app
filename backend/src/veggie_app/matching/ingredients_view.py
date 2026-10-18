"""The "Ingredients view" (see docs design notes, section 2): combines the
protein-substitution score (matching/substitution.py) with the non-protein
FlavorGraph score (matching/ingredient_similarity.py) into a single score
comparing a user's query ingredients against one candidate recipe.

The two sides are handled asymmetrically on purpose:
- The query only has a raw ingredient list, so which word (if any) is
  protein-like has to be *detected* (split_query_ingredients_by_role) — the
  query may even describe a non-vegetarian dish.
- A candidate recipe already has its protein tagged explicitly via
  protein_source (an admin-curated, single vegetarian value — see
  matching/substitution.py's RECIPE_PROTEIN_VOCABULARY), so no detection is
  needed there; it's simply excluded from the "rest" ingredients so it isn't
  scored twice (once as a protein, once as a regular ingredient).

The query side is the same for every candidate of a request, so it is
prepared once (prepare_query_ingredients) and the result reused for each
candidate (prepared_ingredients_view_score).
"""

from dataclasses import dataclass

import numpy as np

from veggie_app.matching.ingredient_names import canonical_name
from veggie_app.matching.ingredient_similarity import ingredient_matrix, matrix_set_similarity
from veggie_app.matching.substitution import (
    protein_set_similarity,
    split_query_ingredients_by_role,
)

DEFAULT_PROTEIN_WEIGHT = 0.4


@dataclass(frozen=True)
class PreparedQueryIngredients:
    """A query's ingredients, split by role and resolved to vectors once."""

    proteins: list[str]
    rest_matrix: np.ndarray


def prepare_query_ingredients(query_ingredients: list[str]) -> PreparedQueryIngredients:
    proteins, rest = split_query_ingredients_by_role(query_ingredients)
    return PreparedQueryIngredients(proteins=proteins, rest_matrix=ingredient_matrix(rest))


def _exclude_protein_source(ingredients: list[str], protein_source: str | None) -> list[str]:
    # Compared on canonical forms: protein_source is written in the unaccented
    # protein vocabulary ("oeuf") while the ingredient list says "œuf".
    if protein_source is None:
        return ingredients
    protein = canonical_name(protein_source)
    return [name for name in ingredients if canonical_name(name) != protein]


def prepared_ingredients_view_score(
    query: PreparedQueryIngredients,
    candidate_ingredients: list[str],
    candidate_protein_source: str | None,
    protein_weight: float = DEFAULT_PROTEIN_WEIGHT,
) -> float:
    """Similarity between a prepared query and one candidate recipe's
    ingredients + protein_source, in [0, 1]. Falls back to the non-protein
    score alone when neither side has a detectable protein — nothing to
    compare there, so it shouldn't drag the overall score down."""
    candidate_proteins = [candidate_protein_source] if candidate_protein_source else []
    candidate_rest = _exclude_protein_source(candidate_ingredients, candidate_protein_source)

    protein_score = protein_set_similarity(query.proteins, candidate_proteins)
    rest_score = matrix_set_similarity(query.rest_matrix, ingredient_matrix(candidate_rest))

    if protein_score is None:
        return rest_score
    return protein_weight * protein_score + (1 - protein_weight) * rest_score


def ingredients_view_score(
    query_ingredients: list[str],
    candidate_ingredients: list[str],
    candidate_protein_source: str | None,
    protein_weight: float = DEFAULT_PROTEIN_WEIGHT,
) -> float:
    """One-off form of prepared_ingredients_view_score, for comparing a raw
    query against a single candidate."""
    return prepared_ingredients_view_score(
        prepare_query_ingredients(query_ingredients),
        candidate_ingredients,
        candidate_protein_source,
        protein_weight,
    )
