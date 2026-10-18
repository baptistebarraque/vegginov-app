import numpy as np
import pytest

from veggie_app.matching.similarity import cosine_similarity, normalize_rows


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


def test_cosine_similarity_accepts_numpy_arrays() -> None:
    assert cosine_similarity(np.array([3.0, 4.0]), np.array([3.0, 4.0])) == pytest.approx(1.0)


def test_normalize_rows_scales_each_row_to_unit_length() -> None:
    normalized = normalize_rows(np.array([[3.0, 4.0], [0.0, 2.0]]))

    assert normalized == pytest.approx(np.array([[0.6, 0.8], [0.0, 1.0]]))


def test_normalize_rows_leaves_zero_rows_at_zero() -> None:
    normalized = normalize_rows(np.array([[0.0, 0.0], [1.0, 0.0]]))

    assert normalized == pytest.approx(np.array([[0.0, 0.0], [1.0, 0.0]]))
