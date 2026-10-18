from collections.abc import Iterator

import numpy as np
import pytest

from veggie_app.matching import ingredient_similarity
from veggie_app.matching.ingredient_similarity import (
    UNIFORM_WEIGHTS,
    IngredientWeights,
    compute_ingredient_weights,
    ingredient_matrix,
    ingredient_set_similarity,
    ingredient_weight_vector,
    matrix_set_similarity,
)

VECTORS = {
    "a1": np.array([1.0, 0.0]),
    "a2": np.array([0.0, 1.0]),
    "b1": np.array([0.0, 1.0]),
    "b2": np.array([1.0, 0.0]),
    "unmapped": None,
}


@pytest.fixture(autouse=True)
def _stub_get_vector(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    # The vector caches would otherwise serve vectors resolved by another test
    # (or the real FlavorGraph data) instead of this stub's.
    ingredient_similarity.clear_vector_caches()
    monkeypatch.setattr(ingredient_similarity, "get_vector", lambda name: VECTORS.get(name))
    # Each stub name is its own concept ("a1" -> "A1"); unmapped has none.
    monkeypatch.setattr(
        ingredient_similarity,
        "get_concept",
        lambda name: name.upper() if VECTORS.get(name) is not None else None,
    )
    yield
    ingredient_similarity.clear_vector_caches()


def test_finds_optimal_assignment_not_naive_order() -> None:
    # a1-b1 / a2-b2 (naive order) are orthogonal (similarity 0 each), but the
    # optimal assignment a1-b2 / a2-b1 is identical (similarity 1 each) — the
    # Hungarian algorithm must find the latter, not just pair by position.
    score = ingredient_set_similarity(["a1", "a2"], ["b1", "b2"])

    assert score == pytest.approx(1.0)


def test_drops_unmapped_ingredients() -> None:
    score = ingredient_set_similarity(["a1", "unmapped"], ["b2"])

    assert score == pytest.approx(1.0)


def test_returns_zero_when_one_side_has_no_resolvable_ingredient() -> None:
    assert ingredient_set_similarity(["unmapped"], ["b1"]) == 0.0
    assert ingredient_set_similarity(["a1"], ["unmapped"]) == 0.0


def test_returns_zero_for_two_empty_lists() -> None:
    assert ingredient_set_similarity([], []) == 0.0


def test_averages_over_matched_pairs_with_uneven_set_sizes() -> None:
    # Only 1 pair can be matched (min(1, 2) = 1); Hungarian picks the best
    # available match for the single left-hand ingredient.
    score = ingredient_set_similarity(["a1"], ["b1", "b2"])

    assert score == pytest.approx(1.0)  # a1 matches b2 (identical), not b1


def test_ingredient_matrix_stacks_resolvable_ingredients_only() -> None:
    matrix = ingredient_matrix(["a1", "unmapped", "a2"])

    assert matrix.shape == (2, 2)


def test_ingredient_matrix_rows_are_unit_length(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(VECTORS, "long", np.array([3.0, 4.0]))

    assert ingredient_matrix(["long"])[0] == pytest.approx([0.6, 0.8])


def test_ingredient_matrix_is_computed_once_per_ingredient_list() -> None:
    first = ingredient_matrix(["a1", "a2"])
    second = ingredient_matrix(["a1", "a2"])

    assert first is second
    assert not first.flags.writeable


def test_ingredient_matrix_of_unresolvable_list_is_empty() -> None:
    assert len(ingredient_matrix(["unmapped"])) == 0


def test_matrix_set_similarity_reuses_a_prepared_query_matrix() -> None:
    query = ingredient_matrix(["a1"])

    assert matrix_set_similarity(query, ingredient_matrix(["b2"])) == pytest.approx(1.0)
    assert matrix_set_similarity(query, ingredient_matrix(["b1"])) == pytest.approx(0.0)


def test_unmatched_query_ingredient_counts_as_zero() -> None:
    # The candidate covers a1 perfectly but has nothing left for a2.
    score = ingredient_set_similarity(["a1", "a2"], ["b2"])

    assert score == pytest.approx(0.5)


def test_weights_decide_how_much_each_query_ingredient_counts() -> None:
    query = ingredient_matrix(["a1", "a2"])
    candidate = ingredient_matrix(["b2"])  # covers a1 only

    score = matrix_set_similarity(query, candidate, np.array([3.0, 1.0]))

    assert score == pytest.approx(3.0 / 4.0)


def test_weighted_assignment_covers_the_heavier_ingredient() -> None:
    # One candidate ingredient, equally close to both query ingredients: it
    # should be spent on the one that weighs more.
    VECTORS["mid"] = np.array([1.0, 1.0])
    try:
        query = ingredient_matrix(["a1", "a2"])
        score = matrix_set_similarity(query, ingredient_matrix(["mid"]), np.array([1.0, 4.0]))
    finally:
        del VECTORS["mid"]

    assert score == pytest.approx(4.0 * 2**-0.5 / 5.0)


def test_negative_similarity_counts_as_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(VECTORS, "opposite", np.array([-1.0, 0.0]))

    assert ingredient_set_similarity(["a1"], ["opposite"]) == 0.0


def test_compute_ingredient_weights_counts_each_recipe_once_per_concept() -> None:
    weights = compute_ingredient_weights([["a1", "a1", "a2"], ["a1"], ["unmapped"]])

    assert weights.recipe_count == 3
    assert weights.document_frequencies == {"A1": 2, "A2": 1}


def test_rarer_ingredients_weigh_more() -> None:
    weights = compute_ingredient_weights([["a1", "a2"], ["a1"], ["a1"]])

    assert weights.weight("a2") > weights.weight("a1")


def test_ingredient_absent_from_corpus_gets_the_median_weight() -> None:
    weights = IngredientWeights(
        document_frequencies={"A1": 1}, recipe_count=4, unknown_weight=1.5
    )

    assert weights.weight("b1") == 1.5  # "B1" is in no recipe


def test_uniform_weights_are_all_one() -> None:
    assert UNIFORM_WEIGHTS.weight("a1") == pytest.approx(1.0)
    assert UNIFORM_WEIGHTS.weight("b1") == pytest.approx(1.0)


def test_ingredient_weight_vector_is_aligned_with_the_matrix_rows() -> None:
    weights = IngredientWeights(document_frequencies={"A1": 1, "A2": 3}, recipe_count=3)

    vector = ingredient_weight_vector(["a1", "unmapped", "a2"], weights)

    assert len(vector) == len(ingredient_matrix(["a1", "unmapped", "a2"]))
    assert vector[0] > vector[1]  # a1 is rarer than a2
