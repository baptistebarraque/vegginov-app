import pytest

from veggie_app.matching import fusion
from veggie_app.matching.fusion import CandidateRecipe, fuse_scores, rank_candidates


def test_fuse_scores_weights_title_and_ingredients() -> None:
    assert fuse_scores(1.0, 0.0, title_weight=0.3) == pytest.approx(0.3)
    assert fuse_scores(0.0, 1.0, title_weight=0.3) == pytest.approx(0.7)


def test_fuse_scores_uses_default_weight() -> None:
    assert fuse_scores(1.0, 0.0) == pytest.approx(fusion.DEFAULT_TITLE_WEIGHT)


@pytest.fixture(autouse=True)
def _stub_ingredients_view(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolates rank_candidates' orchestration (fetching + fusing + sorting)
    from ingredients_view_score's own logic, which has its own test file."""
    monkeypatch.setattr(fusion, "ingredients_view_score", lambda *args, **kwargs: 0.0)


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
    monkeypatch.setattr(fusion, "ingredients_view_score", lambda *args, **kwargs: 1.0)
    candidates = [
        CandidateRecipe(id=1, title_embedding=[1.0, 0.0], ingredient_names=[], protein_source=None),
    ]

    ranked = rank_candidates([1.0, 0.0], [], candidates, title_weight=0.3)

    # title cosine similarity = 1.0, ingredients score stubbed to 1.0 -> fused = 1.0
    assert ranked[0] == (1, pytest.approx(1.0))
