import pytest

from veggie_app.matching import ingredients_view
from veggie_app.matching.ingredients_view import ingredients_view_score


@pytest.fixture(autouse=True)
def _stub_sub_scores(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub out the two underlying views so tests exercise only the
    combination/weighting logic and the query/candidate role-splitting —
    ingredient_set_similarity and protein_set_similarity each have their own
    dedicated test files."""
    monkeypatch.setattr(ingredients_view, "ingredient_set_similarity", lambda a, b: 0.8)
    monkeypatch.setattr(
        ingredients_view, "protein_set_similarity", lambda a, b: 0.6 if a and b else None
    )


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
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = {}

    def fake_ingredient_set_similarity(a: list[str], b: list[str]) -> float:
        captured["query_rest"] = a
        captured["candidate_rest"] = b
        return 0.8

    monkeypatch.setattr(
        ingredients_view, "ingredient_set_similarity", fake_ingredient_set_similarity
    )

    ingredients_view_score(
        query_ingredients=["carotte"],
        candidate_ingredients=["tofu", "curry", "lait de coco"],
        candidate_protein_source="tofu",
    )

    assert captured["candidate_rest"] == ["curry", "lait de coco"]


def test_excludes_query_protein_word_from_query_rest(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    def fake_ingredient_set_similarity(a: list[str], b: list[str]) -> float:
        captured["query_rest"] = a
        return 0.8

    monkeypatch.setattr(
        ingredients_view, "ingredient_set_similarity", fake_ingredient_set_similarity
    )

    ingredients_view_score(
        query_ingredients=["boeuf", "carotte", "oignon"],
        candidate_ingredients=["tofu"],
        candidate_protein_source="tofu",
    )

    assert captured["query_rest"] == ["carotte", "oignon"]
