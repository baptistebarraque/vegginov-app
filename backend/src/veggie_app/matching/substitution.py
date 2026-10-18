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

from functools import lru_cache

import numpy as np
from scipy.optimize import linear_sum_assignment

from veggie_app.matching.ingredient_names import canonical_name

SUBSTITUTION_TABLE: dict[str, list[tuple[str, float]]] = {
    # --- Red meats ---
    "boeuf": [
        ("seitan", 0.90), ("champignon", 0.85), ("proteines de soja texturees", 0.75),
        ("lentilles", 0.65), ("haricots rouges", 0.60), ("jacque", 0.60),
        ("tofu", 0.55), ("haricots noirs", 0.55), ("haricots blancs", 0.50),
        ("pois chiches", 0.45), ("noix", 0.40), ("oeuf", 0.30), ("fromage", 0.30),
    ],
    "viande hachee": [
        ("proteines de soja texturees", 0.85), ("lentilles corail", 0.80),
        ("champignons haches", 0.75), ("haricots rouges", 0.75), ("lentilles", 0.75),
        ("haricots noirs", 0.70), ("seitan hache", 0.70), ("seitan", 0.70),
        ("champignon", 0.70), ("tofu emiette", 0.65), ("quinoa", 0.50), ("oeuf", 0.30),
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
        ("tofu fume", 0.65), ("jacque", 0.60), ("tofu", 0.60), ("haricots blancs", 0.55),
    ],
    # --- Processed meats ---
    "bacon": [
        ("tempeh fume", 0.85), ("tofu fume", 0.75),
        ("champignons shiitake seches", 0.60), ("noix de coco fumee", 0.55),
    ],
    "lardons": [
        ("tempeh fume", 0.80), ("tofu fume", 0.70), ("champignons shiitake seches", 0.55),
        ("oeuf", 0.40),
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
        ("champignon pleurote", 0.70), ("coeur de palmier", 0.65), ("tofu", 0.60),
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


# A specific form of a substitute -> the generic substitute it is a form of.
# The table scores the generic ones against most meats but each specific form
# only against a few ("champignon pleurote" is scored for fish and seafood,
# not for chicken), so a pair with no score of its own falls back to its
# generic form's score rather than to DEFAULT_PROTEIN_SIMILARITY — a pleurote
# is at least as good a stand-in for chicken as "champignon".
SUBSTITUTE_BASES: dict[str, str] = {
    "tofu ferme": "tofu",
    "tofu emiette": "tofu",
    "tofu fume": "tofu",
    "seitan hache": "seitan",
    "seitan epice": "seitan",
    "tempeh fume": "tempeh",
    "champignon pleurote": "champignon",
    "champignons haches": "champignon",
    "champignons shiitake seches": "champignon",
    "haricots rouges epices": "haricots rouges",
    "pois chiches ecrases": "pois chiches",
    "lentilles corail": "lentilles",
}


def _table_score(a: str, b: str, table: dict[str, list[tuple[str, float]]]) -> float | None:
    for name, score in table.get(a, []):
        if name == b:
            return score
    for name, score in table.get(b, []):
        if name == a:
            return score
    return None


def protein_similarity(
    protein_a: str, protein_b: str, table: dict[str, list[tuple[str, float]]] = SUBSTITUTION_TABLE
) -> float:
    """Looks up how good a substitute `protein_b` is for `protein_a` (or vice
    versa — the table is consulted in both directions since either side of a
    comparison could be the meat/fish key or one of its substitutes). A pair
    with no entry of its own is retried with each side's generic form
    (SUBSTITUTE_BASES); only then does it get `DEFAULT_PROTEIN_SIMILARITY`."""
    a, b = protein_a.lower(), protein_b.lower()
    if a == b:
        return 1.0
    score = _table_score(a, b, table)
    if score is None:
        base_a, base_b = SUBSTITUTE_BASES.get(a, a), SUBSTITUTE_BASES.get(b, b)
        if (base_a, base_b) != (a, b):
            score = 1.0 if base_a == base_b else _table_score(base_a, base_b, table)
    return DEFAULT_PROTEIN_SIMILARITY if score is None else score


# Vocabulary used to detect which word(s) in a user's *query* ingredient list
# are protein-like — unlike a recipe's protein_source (an admin-curated,
# single vegetarian value), a query may describe a non-vegetarian dish, so
# both the meat/fish keys and their substitutes are candidates here.
QUERY_PROTEIN_VOCABULARY: frozenset[str] = frozenset(SUBSTITUTION_TABLE.keys()) | frozenset(
    RECIPE_PROTEIN_VOCABULARY
)


# What users actually type for the meats/fish the table knows: cuts, minced
# forms, named sausages, species. Each maps onto an existing SUBSTITUTION_TABLE
# key, so it reuses that key's curated substitutes — a meat with no fitting key
# (duck, rabbit...) belongs in the table with its own scores, not here.
QUERY_PROTEIN_ALIASES: dict[str, str] = {
    # --- Beef cuts ---
    "steak": "boeuf",
    "entrecôte": "boeuf",
    "bavette": "boeuf",
    "rumsteck": "boeuf",
    "faux-filet": "boeuf",
    "paleron": "boeuf",
    "macreuse": "boeuf",
    # --- Minced meat ---
    "steak haché": "viande hachee",
    "bœuf haché": "viande hachee",
    "porc haché": "viande hachee",
    "veau haché": "viande hachee",
    "agneau haché": "viande hachee",
    "chair à saucisse": "saucisse",
    # --- Sausages and cured pork ---
    "chorizo": "saucisse",
    "merguez": "saucisse",
    "chipolata": "saucisse",
    "saucisson": "saucisse",
    "lard": "lardons",
    "poitrine fumée": "lardons",
    "pancetta": "lardons",
    "guanciale": "lardons",
    "prosciutto": "jambon",
    # --- Poultry ---
    "volaille": "poulet",
    # --- Fish ---
    "poisson": "poisson blanc",
    "cabillaud": "poisson blanc",
    "colin": "poisson blanc",
    "merlu": "poisson blanc",
    "lieu": "poisson blanc",
    "églefin": "poisson blanc",
    "haddock": "poisson blanc",
    "dorade": "poisson blanc",
    "daurade": "poisson blanc",
    "bar": "poisson blanc",
    "sole": "poisson blanc",
    "lotte": "poisson blanc",
    "truite": "saumon",
    # --- Seafood ---
    "gambas": "crevettes",
    "fruits de mer": "crevettes",
}

# Head nouns of ingredients that merely *taste of* a meat — a stock, a sauce,
# a fat. "bouillon de poulet" names chicken but carries no chicken protein.
_FLAVORING_HEADS = frozenset(
    canonical_name(head)
    for head in ("bouillon", "cube", "fond", "fumet", "jus", "graisse", "sauce")
)


@lru_cache(maxsize=1)
def _query_protein_index() -> tuple[dict[str, str], list[tuple[list[str], str]]]:
    """(exact, embedded), keyed by canonical_name. `exact` resolves a whole
    ingredient name — any table key, substitute or alias — to the term
    protein_similarity looks up. `embedded` lists the meat/fish terms that
    also count when they appear *inside* a longer name ("cuisses de poulet"),
    longest first so "boeuf hache" wins over "boeuf". Substitutes are
    deliberately exact-only: matched inside a name they misfire on everyday
    compounds ("noix de coco" is not the protein "noix")."""
    exact = {canonical_name(term): term for term in QUERY_PROTEIN_VOCABULARY}
    exact.update({canonical_name(alias): key for alias, key in QUERY_PROTEIN_ALIASES.items()})
    meat_terms = {canonical_name(term) for term in (*SUBSTITUTION_TABLE, *QUERY_PROTEIN_ALIASES)}
    embedded = sorted(
        ((term.split(), exact[term]) for term in meat_terms), key=lambda pair: -len(pair[0])
    )
    return exact, embedded


def _contains_words(words: list[str], term: list[str]) -> bool:
    return any(words[i : i + len(term)] == term for i in range(len(words) - len(term) + 1))


def detect_query_protein(ingredient: str) -> str | None:
    """The protein term (a SUBSTITUTION_TABLE key or substitute) a query
    ingredient names, or None. Spelling-insensitive (canonical_name): "Bœuf"
    and "boeufs" both resolve to "boeuf", "blanc de poulet" to "poulet",
    "saucisses de Toulouse" to "saucisse", "steak haché" to "viande hachee"."""
    exact, embedded = _query_protein_index()
    canonical = canonical_name(ingredient)
    if canonical in exact:
        return exact[canonical]
    words = canonical.split()
    if not words or words[0] in _FLAVORING_HEADS:
        return None
    for term, key in embedded:
        if _contains_words(words, term):
            return key
    return None


def split_query_ingredients_by_role(ingredients: list[str]) -> tuple[list[str], list[str]]:
    """Splits a user's raw ingredient list into (protein terms, rest). The
    proteins come back as the terms protein_similarity looks up (see
    detect_query_protein), each once; the rest keep the user's wording for the
    FlavorGraph lookup. Only needed for the query side — a candidate recipe
    already has its protein tagged explicitly via protein_source."""
    detected = [(ingredient, detect_query_protein(ingredient)) for ingredient in ingredients]
    # When the dish names a meat or fish, that is the protein to replace: the
    # egg in a tonkatsu batter or the beans of a chili are ordinary ingredients
    # of the dish, and treating them as its protein would hand every egg or
    # bean recipe a perfect protein match. Without any meat (a query that is
    # already vegetarian), the vegetarian proteins are the ones to compare.
    names_meat = any(protein in SUBSTITUTION_TABLE for _, protein in detected)
    proteins: list[str] = []
    rest: list[str] = []
    for ingredient, protein in detected:
        if protein is None or (names_meat and protein not in SUBSTITUTION_TABLE):
            rest.append(ingredient)
        elif protein not in proteins:
            proteins.append(protein)
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
    if len(proteins_a) == 1 or len(proteins_b) == 1:
        # Only one pair can be matched, so the Hungarian result is simply the
        # best pair. This is the hot path — a candidate recipe always has a
        # single protein_source — and skipping the matrix setup matters when
        # it runs once per recipe on every request.
        return max(
            protein_similarity(protein_a, protein_b, table)
            for protein_a in proteins_a
            for protein_b in proteins_b
        )

    cost_matrix = np.zeros((len(proteins_a), len(proteins_b)))
    for i, protein_a in enumerate(proteins_a):
        for j, protein_b in enumerate(proteins_b):
            cost_matrix[i, j] = 1 - protein_similarity(protein_a, protein_b, table)

    row_indices, col_indices = linear_sum_assignment(cost_matrix)
    similarities = [
        1 - cost_matrix[r, c] for r, c in zip(row_indices, col_indices, strict=True)
    ]
    return float(np.mean(similarities))
