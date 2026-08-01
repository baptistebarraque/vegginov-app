import numpy as np
import pytest

from veggie_app.matching import ingredient_similarity
from veggie_app.matching.ingredient_similarity import ingredient_set_similarity

VECTORS = {
    "a1": np.array([1.0, 0.0]),
    "a2": np.array([0.0, 1.0]),
    "b1": np.array([0.0, 1.0]),
    "b2": np.array([1.0, 0.0]),
    "unmapped": None,
}


@pytest.fixture(autouse=True)
def _stub_get_vector(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ingredient_similarity, "get_vector", lambda name: VECTORS.get(name))


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
