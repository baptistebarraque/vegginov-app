import pytest

from veggie_app.matching import nutrition_view
from veggie_app.matching.nutrition_view import calorie_orientation_score


def test_exact_bucket_match_scores_one() -> None:
    assert calorie_orientation_score(300.0, "low") == pytest.approx(1.0)
    assert calorie_orientation_score(550.0, "balanced") == pytest.approx(1.0)
    assert calorie_orientation_score(900.0, "high") == pytest.approx(1.0)


def test_adjacent_bucket_scores_half() -> None:
    # recipe is balanced, user wants low (or high) -> one step away.
    assert calorie_orientation_score(550.0, "low") == pytest.approx(0.5)
    assert calorie_orientation_score(550.0, "high") == pytest.approx(0.5)
    # recipe is low, user wants balanced -> one step away.
    assert calorie_orientation_score(300.0, "balanced") == pytest.approx(0.5)


def test_opposite_ends_score_zero() -> None:
    assert calorie_orientation_score(300.0, "high") == pytest.approx(0.0)
    assert calorie_orientation_score(900.0, "low") == pytest.approx(0.0)


def test_bucket_boundaries() -> None:
    # LOW_MAX is exclusive on the low side: exactly LOW_MAX is balanced.
    assert nutrition_view._calorie_bucket(nutrition_view.LOW_MAX) == "balanced"
    assert nutrition_view._calorie_bucket(nutrition_view.LOW_MAX - 0.01) == "low"
    # HIGH_MIN is exclusive on the high side: exactly HIGH_MIN is balanced.
    assert nutrition_view._calorie_bucket(nutrition_view.HIGH_MIN) == "balanced"
    assert nutrition_view._calorie_bucket(nutrition_view.HIGH_MIN + 0.01) == "high"


def test_none_orientation_is_neutral() -> None:
    assert calorie_orientation_score(300.0, None) == nutrition_view.NEUTRAL_SCORE


def test_none_calories_is_neutral() -> None:
    assert calorie_orientation_score(None, "low") == nutrition_view.NEUTRAL_SCORE


def test_unknown_orientation_is_neutral() -> None:
    assert calorie_orientation_score(300.0, "gigantic") == nutrition_view.NEUTRAL_SCORE
