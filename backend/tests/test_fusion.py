import pytest

from veggie_app.matching import fusion
from veggie_app.matching.fusion import (
    CandidateRecipe,
    apply_calorie_orientation,
    fuse_scores,
    rank_candidates,
    title_scores,
)


def test_fuse_scores_weights_title_and_ingredients() -> None:
    assert fuse_scores(1.0, 0.0, title_weight=0.3) == pytest.approx(0.3)
    assert fuse_scores(0.0, 1.0, title_weight=0.3) == pytest.approx(0.7)


def test_fuse_scores_uses_default_weight() -> None:
    assert fuse_scores(1.0, 0.0) == pytest.approx(fusion.DEFAULT_TITLE_WEIGHT)


def test_apply_calorie_orientation_none_returns_similarity_unchanged() -> None:
    assert apply_calorie_orientation(0.8, 300.0, None) == pytest.approx(0.8)


def test_apply_calorie_orientation_blends_matching_bucket() -> None:
    # low-calorie recipe, user wants low -> calorie score 1.0.
    result = apply_calorie_orientation(0.8, 300.0, "low", calorie_weight=0.15)
    assert result == pytest.approx(0.85 * 0.8 + 0.15 * 1.0)


def test_apply_calorie_orientation_penalizes_opposite_bucket() -> None:
    # high-calorie recipe, user wants low -> calorie score 0.0.
    result = apply_calorie_orientation(0.8, 900.0, "low", calorie_weight=0.15)
    assert result == pytest.approx(0.85 * 0.8)


def test_apply_calorie_orientation_missing_calories_is_neutral() -> None:
    # No calorie data -> neutral 0.5, so the recipe isn't buried.
    result = apply_calorie_orientation(0.8, None, "low", calorie_weight=0.15)
    assert result == pytest.approx(0.85 * 0.8 + 0.15 * 0.5)


@pytest.fixture(autouse=True)
def _stub_ingredients_view(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolates rank_candidates' orchestration (fetching + fusing + sorting)
    from prepared_ingredients_view_score's own logic, which has its own test
    file."""
    monkeypatch.setattr(fusion, "prepared_ingredients_view_score", lambda *args, **kwargs: 0.0)


def test_rank_candidates_orders_by_fused_score_descending() -> None:
    query_embedding = [1.0, 0.0]
    candidates = [
        CandidateRecipe(id=1, title_embedding=[0.0, 1.0], ingredient_names=[], protein_source=None),
        CandidateRecipe(id=2, title_embedding=[1.0, 0.0], ingredient_names=[], protein_source=None),
        CandidateRecipe(
            id=3, title_embedding=[-1.0, 0.0], ingredient_names=[], protein_source=None
        ),
    ]

    ranked = rank_candidates(query_embedding, [], candidates, top_k=3)

    assert [candidate_id for candidate_id, _ in ranked] == [2, 1, 3]


def test_rank_candidates_respects_top_k() -> None:
    query_embedding = [1.0, 0.0]
    candidates = [
        CandidateRecipe(id=i, title_embedding=[1.0, 0.0], ingredient_names=[], protein_source=None)
        for i in range(10)
    ]

    ranked = rank_candidates(query_embedding, [], candidates, top_k=4)

    assert len(ranked) == 4


def test_rank_candidates_combines_title_and_ingredients_scores(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(fusion, "prepared_ingredients_view_score", lambda *args, **kwargs: 1.0)
    candidates = [
        CandidateRecipe(id=1, title_embedding=[1.0, 0.0], ingredient_names=[], protein_source=None),
    ]

    ranked = rank_candidates([1.0, 0.0], [], candidates, title_weight=0.3)

    # title cosine similarity = 1.0, ingredients score stubbed to 1.0 -> fused = 1.0
    assert ranked[0] == (1, pytest.approx(1.0))


def test_rank_candidates_orientation_reorders_equal_similarity_candidates() -> None:
    # Two recipes with identical title similarity but different calories: the
    # one matching the "low" orientation should rank first.
    query_embedding = [1.0, 0.0]
    candidates = [
        CandidateRecipe(
            id=1,
            title_embedding=[1.0, 0.0],
            ingredient_names=[],
            protein_source=None,
            calories_per_portion=900.0,  # high
        ),
        CandidateRecipe(
            id=2,
            title_embedding=[1.0, 0.0],
            ingredient_names=[],
            protein_source=None,
            calories_per_portion=300.0,  # low
        ),
    ]

    ranked = rank_candidates(query_embedding, [], candidates, calorie_orientation="low")

    assert [candidate_id for candidate_id, _ in ranked] == [2, 1]


def test_rank_candidates_without_orientation_ignores_calories() -> None:
    # Same two recipes, no orientation -> calories don't matter, order is stable.
    query_embedding = [1.0, 0.0]
    candidates = [
        CandidateRecipe(
            id=1, title_embedding=[1.0, 0.0], ingredient_names=[], protein_source=None,
            calories_per_portion=900.0,
        ),
        CandidateRecipe(
            id=2, title_embedding=[1.0, 0.0], ingredient_names=[], protein_source=None,
            calories_per_portion=300.0,
        ),
    ]

    ranked = rank_candidates(query_embedding, [], candidates)

    assert all(score == pytest.approx(ranked[0][1]) for _, score in ranked)


def test_title_scores_returns_cosine_per_candidate_in_order() -> None:
    candidates = [
        CandidateRecipe(id=1, title_embedding=[0.0, 2.0], ingredient_names=[], protein_source=None),
        CandidateRecipe(id=2, title_embedding=[3.0, 0.0], ingredient_names=[], protein_source=None),
        CandidateRecipe(id=3, title_embedding=[1.0, 1.0], ingredient_names=[], protein_source=None),
    ]

    scores = title_scores([5.0, 0.0], candidates)

    # Unnormalized inputs on purpose: the scores are cosines, not dot products.
    assert list(scores) == pytest.approx([0.0, 1.0, 2**-0.5])


def test_title_scores_zero_query_vector_scores_zero() -> None:
    candidates = [
        CandidateRecipe(id=1, title_embedding=[1.0, 0.0], ingredient_names=[], protein_source=None),
    ]

    assert list(title_scores([0.0, 0.0], candidates)) == [0.0]


def test_rank_candidates_with_no_candidates_returns_empty() -> None:
    assert rank_candidates([1.0, 0.0], ["oignon"], []) == []


def test_rank_candidates_prepares_query_ingredients_once(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []

    def fake_prepare(query_ingredients: list[str]) -> str:
        calls.append(query_ingredients)
        return "prepared"

    monkeypatch.setattr(fusion, "prepare_query_ingredients", fake_prepare)
    candidates = [
        CandidateRecipe(id=i, title_embedding=[1.0, 0.0], ingredient_names=[], protein_source=None)
        for i in range(5)
    ]

    rank_candidates([1.0, 0.0], ["oignon"], candidates)

    assert calls == [["oignon"]]
