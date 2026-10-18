import pytest

from veggie_app.matching import ingredients_view
from veggie_app.matching.ingredients_view import (
    ingredients_view_score,
    prepare_query_ingredients,
    prepared_ingredients_view_score,
)


@pytest.fixture(autouse=True)
def matrix_calls(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Stubs out the two underlying views so tests exercise only the
    combination/weighting logic and the query/candidate role-splitting —
    the ingredient matrices and protein_set_similarity each have their own
    dedicated test files. The fake ingredient_matrix returns the names it was
    given, and every call is recorded in the returned list."""
    calls: list[list[str]] = []

    def fake_ingredient_matrix(names: list[str]) -> list[str]:
        calls.append(list(names))
        return list(names)

    monkeypatch.setattr(ingredients_view, "ingredient_matrix", fake_ingredient_matrix)
    monkeypatch.setattr(ingredients_view, "matrix_set_similarity", lambda a, b: 0.8)
    monkeypatch.setattr(
        ingredients_view, "protein_set_similarity", lambda a, b: 0.6 if a and b else None
    )
    return calls


def test_combines_both_scores_with_default_weight() -> None:
    score = ingredients_view_score(
        query_ingredients=["boeuf", "carotte"],
        candidate_ingredients=["tofu", "curry"],
        candidate_protein_source="tofu",
    )

    # default protein_weight = 0.4: 0.4 * 0.6 + 0.6 * 0.8
    assert score == pytest.approx(0.4 * 0.6 + 0.6 * 0.8)


def test_respects_custom_protein_weight() -> None:
    score = ingredients_view_score(
        query_ingredients=["boeuf"],
        candidate_ingredients=["tofu"],
        candidate_protein_source="tofu",
        protein_weight=0.9,
    )

    assert score == pytest.approx(0.9 * 0.6 + 0.1 * 0.8)


def test_falls_back_to_rest_score_when_no_protein_detected_on_either_side() -> None:
    score = ingredients_view_score(
        query_ingredients=["carotte", "oignon"],
        candidate_ingredients=["curry", "lait de coco"],
        candidate_protein_source=None,
    )

    assert score == 0.8


def test_excludes_candidate_protein_source_from_rest_ingredients(
    matrix_calls: list[list[str]],
) -> None:
    ingredients_view_score(
        query_ingredients=["carotte"],
        candidate_ingredients=["tofu", "curry", "lait de coco"],
        candidate_protein_source="tofu",
    )

    assert matrix_calls[-1] == ["curry", "lait de coco"]


def test_excludes_query_protein_word_from_query_rest(matrix_calls: list[list[str]]) -> None:
    prepared = prepare_query_ingredients(["boeuf", "carotte", "oignon"])

    assert prepared.proteins == ["boeuf"]
    assert matrix_calls == [["carotte", "oignon"]]


def test_prepared_query_is_reused_across_candidates(matrix_calls: list[list[str]]) -> None:
    prepared = prepare_query_ingredients(["boeuf", "carotte"])

    for candidate in (["curry"], ["lait de coco"], ["riz"]):
        prepared_ingredients_view_score(prepared, candidate, None)

    # One matrix for the query, then one per candidate — the query's rest
    # ingredients are never resolved again.
    assert matrix_calls == [["carotte"], ["curry"], ["lait de coco"], ["riz"]]


def test_excludes_candidate_protein_source_whatever_its_spelling(
    matrix_calls: list[list[str]],
) -> None:
    # protein_source uses the unaccented vocabulary, the ingredient list doesn't.
    ingredients_view_score(
        query_ingredients=["carotte"],
        candidate_ingredients=["œufs", "poireau"],
        candidate_protein_source="oeuf",
    )

    assert matrix_calls[-1] == ["poireau"]
