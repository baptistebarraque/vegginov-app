import pytest

from veggie_app.matching.similarity import cosine_similarity, rank_by_similarity


def test_cosine_similarity_identical_vectors() -> None:
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)


def test_cosine_similarity_orthogonal_vectors() -> None:
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_cosine_similarity_opposite_vectors() -> None:
    assert cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)


def test_cosine_similarity_zero_vector_returns_zero() -> None:
    assert cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0


def test_cosine_similarity_dimension_mismatch_raises() -> None:
    with pytest.raises(ValueError):
        cosine_similarity([1.0, 0.0], [1.0, 0.0, 0.0])


def test_rank_by_similarity_orders_by_score_descending() -> None:
    query = [1.0, 0.0]
    candidates = [
        (1, [0.0, 1.0]),  # orthogonal -> 0
        (2, [1.0, 0.0]),  # identical -> 1
        (3, [-1.0, 0.0]),  # opposite -> -1
    ]

    ranked = rank_by_similarity(query, candidates, top_k=3)

    assert [candidate_id for candidate_id, _ in ranked] == [2, 1, 3]


def test_rank_by_similarity_respects_top_k() -> None:
    query = [1.0, 0.0]
    candidates = [(i, [1.0, 0.0]) for i in range(10)]

    ranked = rank_by_similarity(query, candidates, top_k=4)

    assert len(ranked) == 4
