import pytest

from veggie_app.matching.ingredient_names import canonical_name
from veggie_app.matching.substitution import (
    DEFAULT_PROTEIN_SIMILARITY,
    QUERY_PROTEIN_ALIASES,
    QUERY_PROTEIN_VOCABULARY,
    RECIPE_PROTEIN_VOCABULARY,
    SUBSTITUTE_BASES,
    SUBSTITUTION_TABLE,
    _query_protein_index,
    detect_query_protein,
    protein_set_similarity,
    protein_similarity,
    split_query_ingredients_by_role,
)


def test_protein_similarity_identical_names_is_one() -> None:
    assert protein_similarity("tofu", "tofu") == 1.0


def test_protein_similarity_is_case_insensitive() -> None:
    assert protein_similarity("Tofu", "TOFU") == 1.0


def test_protein_similarity_looks_up_table_entry() -> None:
    assert protein_similarity("boeuf", "seitan") == 0.90


def test_protein_similarity_looks_up_reverse_direction() -> None:
    assert protein_similarity("seitan", "boeuf") == 0.90


def test_protein_similarity_defaults_for_unknown_pair() -> None:
    assert protein_similarity("boeuf", "courgette") == DEFAULT_PROTEIN_SIMILARITY


def test_recipe_protein_vocabulary_contains_substitute_names_only() -> None:
    assert "tofu" in RECIPE_PROTEIN_VOCABULARY
    assert "seitan" in RECIPE_PROTEIN_VOCABULARY
    # Meat/fish keys are what gets substituted, never a vegetarian recipe's
    # own protein_source, so they shouldn't leak into this vocabulary.
    assert "boeuf" not in RECIPE_PROTEIN_VOCABULARY
    assert "poulet" not in RECIPE_PROTEIN_VOCABULARY


def test_recipe_protein_vocabulary_is_sorted_and_deduplicated() -> None:
    assert list(RECIPE_PROTEIN_VOCABULARY) == sorted(set(RECIPE_PROTEIN_VOCABULARY))


@pytest.mark.parametrize(
    "protein", ["oeuf", "fromage", "haricots noirs", "haricots blancs", "noix", "quinoa"]
)
def test_recipe_protein_vocabulary_covers_native_vegetarian_proteins(protein: str) -> None:
    """Half the real vegetarian corpus takes its protein from eggs, cheese,
    beans or nuts rather than from a meat substitute. A value missing here
    cannot be stored as a recipe's protein_source at all (validate_protein_source
    rejects it), which would leave those recipes permanently untagged."""
    assert protein in RECIPE_PROTEIN_VOCABULARY


@pytest.mark.parametrize(
    "protein", ["oeuf", "fromage", "haricots noirs", "haricots blancs", "noix", "quinoa"]
)
def test_native_vegetarian_proteins_beat_the_unknown_pair_default(protein: str) -> None:
    """Each of these must relate to at least one meat, not sit at the default.
    ingredients_view.py skips the protein view entirely for a recipe with no
    protein_source, so an untagged recipe scores neutrally; a tagged one whose
    protein matches nothing would score DEFAULT_PROTEIN_SIMILARITY and rank
    *below* it. Tagging must not be a penalty."""
    best = max(protein_similarity(meat, protein) for meat in SUBSTITUTION_TABLE)
    assert best > DEFAULT_PROTEIN_SIMILARITY


def test_recipe_protein_vocabulary_covers_every_table_substitute() -> None:
    all_substitutes = {name for entries in SUBSTITUTION_TABLE.values() for name, _ in entries}
    assert set(RECIPE_PROTEIN_VOCABULARY) == all_substitutes


def test_query_protein_vocabulary_includes_both_meat_keys_and_substitutes() -> None:
    assert "boeuf" in QUERY_PROTEIN_VOCABULARY  # a meat key (query may be non-vegetarian)
    assert "tofu" in QUERY_PROTEIN_VOCABULARY  # a substitute


def test_split_query_ingredients_by_role_separates_protein_from_rest() -> None:
    proteins, rest = split_query_ingredients_by_role(["boeuf", "carotte", "oignon"])

    assert proteins == ["boeuf"]
    assert rest == ["carotte", "oignon"]


def test_split_query_ingredients_by_role_is_case_insensitive() -> None:
    proteins, _rest = split_query_ingredients_by_role(["BOEUF"])

    # Returned as the term protein_similarity looks up, not as typed.
    assert proteins == ["boeuf"]


def test_split_query_ingredients_by_role_handles_no_protein() -> None:
    proteins, rest = split_query_ingredients_by_role(["carotte", "oignon"])

    assert proteins == []
    assert rest == ["carotte", "oignon"]


def test_protein_set_similarity_returns_none_when_either_side_is_empty() -> None:
    assert protein_set_similarity([], ["tofu"]) is None
    assert protein_set_similarity(["boeuf"], []) is None
    assert protein_set_similarity([], []) is None


def test_protein_set_similarity_matches_single_pair() -> None:
    assert protein_set_similarity(["boeuf"], ["seitan"]) == pytest.approx(0.90)


def test_protein_set_similarity_picks_best_match_among_several_query_words() -> None:
    # "carotte" isn't protein-like at all (low default score against "tofu"),
    # but "boeuf" is a good match for "tofu" (0.55) — the best pairing should
    # win, not an arbitrary or first-listed one.
    score = protein_set_similarity(["carotte", "boeuf"], ["tofu"])

    assert score == pytest.approx(0.55)


def test_protein_set_similarity_finds_optimal_assignment_between_several_on_each_side() -> None:
    # Greedy would pair boeuf-seitan (0.90) then leave poulet-tofu (0.80);
    # here that greedy pairing is also optimal (0.85 mean) and must beat the
    # crossed pairing boeuf-tofu (0.55) + poulet-seitan (0.80) = 0.675 mean.
    score = protein_set_similarity(["boeuf", "poulet"], ["tofu", "seitan"])

    assert score == pytest.approx((0.90 + 0.80) / 2)



@pytest.mark.parametrize(
    ("written", "term"),
    [
        ("bœuf", "boeuf"),
        ("Boeufs", "boeuf"),
        ("crevette", "crevettes"),
        ("viande hachée", "viande hachee"),
        ("œufs", "oeuf"),
        ("Pois chiche", "pois chiches"),
    ],
)
def test_detect_query_protein_ignores_spelling(written: str, term: str) -> None:
    assert detect_query_protein(written) == term


@pytest.mark.parametrize(
    ("written", "term"),
    [
        ("blanc de poulet", "poulet"),
        ("cuisses de poulet", "poulet"),
        ("épaule d'agneau", "agneau"),
        ("saucisses de Toulouse", "saucisse"),
        ("lardons fumés", "lardons"),
        ("thon en boîte", "thon"),
    ],
)
def test_detect_query_protein_finds_a_meat_inside_a_longer_name(written: str, term: str) -> None:
    assert detect_query_protein(written) == term


@pytest.mark.parametrize(
    ("written", "term"),
    [
        ("chorizo", "saucisse"),
        ("cabillaud", "poisson blanc"),
        ("steak de bœuf", "boeuf"),
        # The longest term wins: minced, not just "steak"/"boeuf".
        ("steak haché", "viande hachee"),
        ("bœuf haché", "viande hachee"),
        ("filet de dorade", "poisson blanc"),
    ],
)
def test_detect_query_protein_resolves_cuts_and_species(written: str, term: str) -> None:
    assert detect_query_protein(written) == term


@pytest.mark.parametrize("written", ["bouillon de poulet", "fond de veau", "sauce de poisson"])
def test_detect_query_protein_ignores_stocks_and_sauces(written: str) -> None:
    assert detect_query_protein(written) is None


@pytest.mark.parametrize("written", ["noix de coco", "fromage blanc", "huile de noix"])
def test_detect_query_protein_matches_substitutes_only_as_whole_names(written: str) -> None:
    assert detect_query_protein(written) is None


def test_detect_query_protein_returns_none_for_an_ordinary_ingredient() -> None:
    assert detect_query_protein("carottes") is None


def test_query_protein_aliases_point_at_table_keys() -> None:
    assert set(QUERY_PROTEIN_ALIASES.values()) <= set(SUBSTITUTION_TABLE)


def test_query_protein_index_has_no_ambiguous_spelling() -> None:
    """No two vocabulary entries or aliases may share a canonical form while
    meaning different terms — one of them would silently become unreachable."""
    terms: dict[str, set[str]] = {}
    for term in QUERY_PROTEIN_VOCABULARY:
        terms.setdefault(canonical_name(term), set()).add(term)
    for alias, key in QUERY_PROTEIN_ALIASES.items():
        terms.setdefault(canonical_name(alias), set()).add(key)

    assert {form: found for form, found in terms.items() if len(found) > 1} == {}
    assert _query_protein_index()[0]  # the index builds


def test_split_query_ingredients_by_role_lists_each_protein_once() -> None:
    proteins, rest = split_query_ingredients_by_role(["poulet", "blanc de poulet", "riz"])

    assert proteins == ["poulet"]
    assert rest == ["riz"]


def test_split_query_ingredients_by_role_keeps_meat_as_the_only_protein() -> None:
    # The egg of a tonkatsu batter is an ingredient of the dish, not the
    # protein to replace.
    proteins, rest = split_query_ingredients_by_role(["côtelettes de porc", "œuf", "farine"])

    assert proteins == ["porc"]
    assert rest == ["œuf", "farine"]


def test_split_query_ingredients_by_role_without_meat_keeps_vegetarian_proteins() -> None:
    proteins, rest = split_query_ingredients_by_role(["tofu", "riz"])

    assert proteins == ["tofu"]
    assert rest == ["riz"]


def test_protein_similarity_falls_back_to_the_generic_substitute() -> None:
    # Only "champignon" is scored for poulet; a pleurote borrows that score.
    assert protein_similarity("poulet", "champignon pleurote") == pytest.approx(
        protein_similarity("poulet", "champignon")
    )


def test_protein_similarity_prefers_a_specific_score_over_the_fallback() -> None:
    # poisson blanc scores the pleurote itself (0.55) — that entry wins.
    assert protein_similarity("poisson blanc", "champignon pleurote") == pytest.approx(0.55)


def test_protein_similarity_treats_two_forms_of_one_substitute_as_identical() -> None:
    assert protein_similarity("tofu ferme", "tofu emiette") == 1.0


def test_protein_similarity_still_defaults_for_a_true_gap() -> None:
    assert protein_similarity("boeuf", "coeur de palmier") == DEFAULT_PROTEIN_SIMILARITY


def test_substitute_bases_stay_inside_the_recipe_vocabulary() -> None:
    assert set(SUBSTITUTE_BASES) <= set(RECIPE_PROTEIN_VOCABULARY)
    assert set(SUBSTITUTE_BASES.values()) <= set(RECIPE_PROTEIN_VOCABULARY)
