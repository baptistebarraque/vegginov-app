"""Protein-source similarity: a hand-curated meat/fish -> vegetarian
substitution table, not an embedding. This is a small, closed problem (a
few dozen entries) where direct curation is more reliable than an
embedding trained for a different purpose (ingredient co-occurrence).

Scored on a 0-1 scale: seitan/tofu ~0.75-0.90 (closest texture, versatile),
mushroom ~0.55-0.85 depending on the dish, legumes ~0.45-0.80 depending on
target texture, specialized substitutes reserved for cases where texture is
decisive. Assumes an ovo-lacto-vegetarian app (eggs/dairy allowed, only
meat/fish are substituted) — consistent with docs/ROADMAP.md, which keeps
a vegan extension as a separate later phase.

Eggs, cheese, nuts, quinoa and the non-red beans sit lower (0.30-0.55) and are
listed for a different reason than the rest: they are rarely chosen as a
*texture* replacement, but they are what actually carries the protein in half
of the real vegetarian corpus (measured on the 4087-recipe Epicurious import —
only 12% of those recipes contain one of the meat-substitute values, while ~50%
run on egg/cheese/beans/nuts). They have to appear here because
RECIPE_PROTEIN_VOCABULARY is derived from this table's values: a value absent
from it cannot be stored as a recipe's protein_source at all. Leaving them out
was worse than a missing tag — ingredients_view.py skips the protein view
entirely when a recipe has no protein_source, so an untagged recipe scores
neutrally while a tagged one with no table entry would score
DEFAULT_PROTEIN_SIMILARITY. Tagging half the corpus without these entries would
therefore have pushed exactly those recipes *down* the ranking.
"""

import numpy as np
from scipy.optimize import linear_sum_assignment

SUBSTITUTION_TABLE: dict[str, list[tuple[str, float]]] = {
    # --- Red meats ---
    "boeuf": [
        ("seitan", 0.90), ("champignon", 0.85), ("lentilles", 0.65),
        ("haricots rouges", 0.60), ("tofu", 0.55), ("haricots noirs", 0.55),
        ("haricots blancs", 0.50), ("pois chiches", 0.45), ("noix", 0.40),
        ("oeuf", 0.30), ("fromage", 0.30),
    ],
    "viande hachee": [
        ("proteines de soja texturees", 0.85), ("lentilles corail", 0.80),
        ("champignons haches", 0.75), ("haricots rouges", 0.75),
        ("haricots noirs", 0.70), ("seitan hache", 0.70), ("tofu emiette", 0.65),
        ("quinoa", 0.50), ("oeuf", 0.30),
    ],
    "agneau": [
        ("champignon", 0.75), ("seitan", 0.75), ("pois chiches", 0.65),
        ("haricots rouges", 0.60), ("haricots blancs", 0.55), ("aubergine", 0.55),
    ],
    "veau": [
        ("seitan", 0.70), ("champignon", 0.65), ("tofu", 0.60), ("pois chiches", 0.50),
        ("oeuf", 0.40), ("fromage", 0.40),
    ],
    "porc": [
        ("seitan", 0.75), ("champignon", 0.70), ("tempeh", 0.65),
        ("tofu fume", 0.65), ("jacque", 0.60), ("haricots blancs", 0.55),
    ],
    # --- Processed meats ---
    "bacon": [
        ("tempeh fume", 0.85), ("tofu fume", 0.75),
        ("champignons shiitake seches", 0.60), ("noix de coco fumee", 0.55),
    ],
    "lardons": [
        ("tempeh fume", 0.80), ("tofu fume", 0.70), ("champignons shiitake seches", 0.55),
    ],
    "saucisse": [
        ("seitan epice", 0.80), ("proteines de soja texturees", 0.75),
        ("haricots rouges epices", 0.55), ("haricots blancs", 0.55),
    ],
    "jambon": [
        ("tofu fume", 0.65), ("seitan", 0.60), ("champignon", 0.55),
        ("fromage", 0.50), ("oeuf", 0.45),
    ],
    # --- Poultry ---
    "poulet": [
        ("tofu", 0.80), ("seitan", 0.80), ("jacque", 0.75),
        ("pois chiches", 0.65), ("champignon", 0.55), ("oeuf", 0.50),
        ("fromage", 0.45), ("quinoa", 0.45), ("haricots blancs", 0.45),
        ("noix", 0.40),
    ],
    "dinde": [
        ("seitan", 0.80), ("tofu", 0.75), ("pois chiches", 0.60),
        ("oeuf", 0.45), ("quinoa", 0.45),
    ],
    # --- Fish and seafood ---
    "poisson blanc": [
        ("coeur de palmier", 0.70), ("champignon pleurote", 0.55), ("tofu ferme", 0.55),
    ],
    "saumon": [
        ("carotte fumee", 0.60), ("tomate marinee", 0.55), ("tofu fume", 0.50),
    ],
    "thon": [
        ("pois chiches ecrases", 0.70), ("tomate marinee", 0.55), ("jacque", 0.50),
    ],
    "crevettes": [
        ("champignon pleurote", 0.70), ("coeur de palmier", 0.65),
    ],
    "moules": [
        ("champignon pleurote", 0.60), ("coeur de palmier", 0.55),
    ],
}

# Vocabulary offered when tagging a recipe's own `protein_source`: since every
# recipe in the database is already vegetarian, its protein is one of the
# substitutes (the table's values), never one of the meat/fish being
# substituted (the table's keys) — those keys only matter later, for
# interpreting a user's (possibly non-vegetarian) query.
RECIPE_PROTEIN_VOCABULARY: tuple[str, ...] = tuple(
    sorted(
        {substitute for substitutes in SUBSTITUTION_TABLE.values() for substitute, _ in substitutes}
    )
)

DEFAULT_PROTEIN_SIMILARITY = 0.1


def protein_similarity(
    protein_a: str, protein_b: str, table: dict[str, list[tuple[str, float]]] = SUBSTITUTION_TABLE
) -> float:
    """Looks up how good a substitute `protein_b` is for `protein_a` (or vice
    versa — the table is consulted in both directions since either side of a
    comparison could be the meat/fish key or one of its substitutes).
    Returns `DEFAULT_PROTEIN_SIMILARITY` for a pair with no table entry."""
    a, b = protein_a.lower(), protein_b.lower()
    if a == b:
        return 1.0
    for name, score in table.get(a, []):
        if name == b:
            return score
    for name, score in table.get(b, []):
        if name == a:
            return score
    return DEFAULT_PROTEIN_SIMILARITY


# Vocabulary used to detect which word(s) in a user's *query* ingredient list
# are protein-like — unlike a recipe's protein_source (an admin-curated,
# single vegetarian value), a query may describe a non-vegetarian dish, so
# both the meat/fish keys and their substitutes are candidates here.
QUERY_PROTEIN_VOCABULARY: frozenset[str] = frozenset(SUBSTITUTION_TABLE.keys()) | frozenset(
    RECIPE_PROTEIN_VOCABULARY
)


def split_query_ingredients_by_role(
    ingredients: list[str], vocabulary: frozenset[str] = QUERY_PROTEIN_VOCABULARY
) -> tuple[list[str], list[str]]:
    """Splits a user's raw ingredient list into (protein-like, rest). Only
    needed for the query side — a candidate recipe already has its protein
    tagged explicitly via protein_source, no detection required."""
    proteins = [ingredient for ingredient in ingredients if ingredient.lower() in vocabulary]
    rest = [ingredient for ingredient in ingredients if ingredient.lower() not in vocabulary]
    return proteins, rest


def protein_set_similarity(
    proteins_a: list[str],
    proteins_b: list[str],
    table: dict[str, list[tuple[str, float]]] = SUBSTITUTION_TABLE,
) -> float | None:
    """Best-match protein similarity between two sets, via the Hungarian
    algorithm — this naturally reduces to "best of several" when one side
    has more entries than the other (e.g. multiple query words detected as
    protein-like vs. a candidate's single protein_source). Returns None if
    either side has no protein at all, so callers can skip this view rather
    than penalize a recipe for lacking one."""
    if not proteins_a or not proteins_b:
        return None

    cost_matrix = np.zeros((len(proteins_a), len(proteins_b)))
    for i, protein_a in enumerate(proteins_a):
        for j, protein_b in enumerate(proteins_b):
            cost_matrix[i, j] = 1 - protein_similarity(protein_a, protein_b, table)

    row_indices, col_indices = linear_sum_assignment(cost_matrix)
    similarities = [
        1 - cost_matrix[r, c] for r, c in zip(row_indices, col_indices, strict=True)
    ]
    return float(np.mean(similarities))
