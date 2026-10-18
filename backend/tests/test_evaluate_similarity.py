import json
import math

import pytest

from scripts import evaluate_similarity
from scripts.evaluate_similarity import (
    DEFAULT_QUERIES_PATH,
    evaluate_ranking,
    grades_in_rank_order,
    hit_at_k,
    load_queries,
    ndcg_at_k,
    recall_at_k,
    reciprocal_rank,
    summarize,
)


def test_reciprocal_rank_uses_first_relevant_position() -> None:
    assert reciprocal_rank([0, 0, 1, 2]) == pytest.approx(1 / 3)


def test_reciprocal_rank_is_zero_without_relevant_item() -> None:
    assert reciprocal_rank([0, 0, 0]) == 0.0


def test_hit_at_k_only_looks_at_first_k() -> None:
    assert hit_at_k([0, 0, 0, 0, 2], k=4) is False
    assert hit_at_k([0, 0, 0, 1], k=4) is True


def test_hit_at_k_respects_min_grade() -> None:
    assert hit_at_k([1, 1, 0, 0], k=4, min_grade=2) is False
    assert hit_at_k([1, 2, 0, 0], k=4, min_grade=2) is True


def test_recall_at_k_counts_relevant_in_top_k() -> None:
    assert recall_at_k([2, 0, 1, 0, 1], relevant_count=4, k=3) == pytest.approx(2 / 4)


def test_recall_at_k_with_nothing_judged_is_zero() -> None:
    assert recall_at_k([0, 0], relevant_count=0, k=2) == 0.0


def test_ndcg_is_one_for_ideal_order() -> None:
    assert ndcg_at_k([2, 1, 1, 0], judged_grades=[1, 2, 1], k=12) == pytest.approx(1.0)


def test_ndcg_penalizes_ideal_recipe_ranked_late() -> None:
    # Grade-2 recipe at rank 2 instead of 1: DCG = 1 + 3/log2(3), ideal 3 + 1/log2(3).
    expected = (1 + 3 / math.log2(3)) / (3 + 1 / math.log2(3))

    assert ndcg_at_k([1, 2], judged_grades=[2, 1], k=12) == pytest.approx(expected)


def test_ndcg_with_nothing_judged_is_zero() -> None:
    assert ndcg_at_k([0, 0], judged_grades=[], k=12) == 0.0


def test_grades_in_rank_order_credits_duplicate_title_once() -> None:
    grades = grades_in_rank_order(["Dahl", "Chili", "Dahl"], {"Dahl": 2})

    assert grades == [2, 0, 0]


def test_evaluate_ranking_reports_ranks_and_metrics() -> None:
    ranked = ["Chili", "Gratin", "Bourguignon de seitan", "Ratatouille", "Pot-au-feu"]
    relevant = {"Bourguignon de seitan": 2, "Pot-au-feu": 1, "Absente": 1}

    result = evaluate_ranking("boeuf", ["boeuf"], ranked, relevant)

    assert result.first_relevant_rank == 3
    assert result.reciprocal_rank == pytest.approx(1 / 3)
    assert result.hit_at_4 is True
    assert result.ideal_at_4 is True
    assert result.recall_at_12 == pytest.approx(2 / 3)
    assert result.judged_ranks == {"Bourguignon de seitan": 3, "Pot-au-feu": 5, "Absente": None}


def test_evaluate_ranking_ideal_is_not_applicable_without_grade_two() -> None:
    result = evaluate_ranking("moules", [], ["Pleurotes"], {"Pleurotes": 1})

    assert result.ideal_at_4 is None


def test_summarize_skips_not_applicable_values() -> None:
    with_ideal = evaluate_ranking("a", [], ["X"], {"X": 2})
    without_ideal = evaluate_ranking("b", [], ["Y"], {"Z": 1})

    summary = summarize([with_ideal, without_ideal])

    assert summary["ideal_at_4"] == 1.0  # only query "a" counts
    assert summary["hit_at_4"] == 0.5


def test_queries_file_is_well_formed() -> None:
    queries = load_queries(DEFAULT_QUERIES_PATH)
    ids = [query["id"] for query in queries]

    assert len(ids) == len(set(ids)), "query ids must be unique"
    for query in queries:
        assert query["title"].strip()
        assert isinstance(query["ingredients"], list)
        assert query["tags"]
        assert query["relevant"], f"{query['id']} judges no recipe"
        assert set(query["relevant"].values()) <= {1, 2}, query["id"]


def test_main_stops_when_a_judged_title_is_not_in_the_database(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pytest.TempPathFactory
) -> None:
    queries_path = tmp_path / "queries.json"
    queries_path.write_text(
        json.dumps(
            {
                "queries": [
                    {
                        "id": "q",
                        "title": "Chili",
                        "ingredients": [],
                        "tags": ["boeuf"],
                        "relevant": {"Recette fantôme": 2},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    class FakeSession:
        def execute(self, statement: object) -> "FakeSession":
            return self

        def scalars(self) -> "FakeSession":
            return self

        def all(self) -> list:
            return []

        def close(self) -> None:
            pass

    monkeypatch.setattr(evaluate_similarity, "SessionLocal", FakeSession)
    monkeypatch.setattr("sys.argv", ["evaluate_similarity", "--queries", str(queries_path)])

    assert evaluate_similarity.main() == 1
