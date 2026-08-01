import pytest

from veggie_app.matching.substitution import (
    DEFAULT_PROTEIN_SIMILARITY,
    QUERY_PROTEIN_VOCABULARY,
    RECIPE_PROTEIN_VOCABULARY,
    SUBSTITUTION_TABLE,
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

    assert proteins == ["BOEUF"]


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
