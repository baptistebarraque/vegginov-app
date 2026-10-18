"""Measures recipe-similarity quality against a judged query set.

Run with (database up, from backend/):
    uv run python -m scripts.evaluate_similarity
    uv run python -m scripts.evaluate_similarity -v                # + top 4 of each query
    uv run python -m scripts.evaluate_similarity --query boeuf-bourguignon -v
    uv run python -m scripts.evaluate_similarity --save before.json
    uv run python -m scripts.evaluate_similarity --compare before.json

Each query in data/similarity_eval/queries.json is a non-vegetarian dish typed
the way a user would type it, with the recipes that *should* come back, graded
2 (the vegetarian version of the dish) or 1 (a suggestion the user would be
happy with). Every query is ranked against the whole recipe table through the
same code path as /suggestions (recipe_service.build_candidate +
fusion.rank_candidates, stored title embeddings), but without user preferences:
this measures similarity alone, not allergen/price filtering.

Metrics, averaged over queries:
* hit@4      — a relevant recipe is among the first 4 suggestions.
* ideal@4    — a grade-2 recipe is among the first 4 (only over queries that
               have one).
* MRR        — mean of 1 / rank of the first relevant recipe.
* nDCG@12    — graded ranking quality of the 12 suggestions /suggestions
               returns (1.0 = the judged recipes, best grade first).
* recall@12  — share of the judged recipes found in those 12.

Unjudged recipes count as not relevant, so a good suggestion that nobody judged
yet lowers the score: when -v shows one, add it to queries.json rather than
treating the drop as a regression. --save / --compare keep one run's results so
a matching change can be judged by its effect on every query, not only on the
two or three tried by hand.
"""

import argparse
import json
import logging
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean

from sqlalchemy import select

from veggie_app.database import SessionLocal
from veggie_app.matching.embeddings import embed_text
from veggie_app.matching.fusion import rank_candidates
from veggie_app.models.recipe import Recipe
from veggie_app.services import recipe_service

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = False
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(_handler)

BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_QUERIES_PATH = BACKEND_DIR / "data" / "similarity_eval" / "queries.json"

# The first screen of suggestions, and the full page /suggestions returns.
FIRST_SCREEN = 4
PAGE_SIZE = recipe_service.SUGGESTION_COUNT

IDEAL_GRADE = 2
GRADE_MARKS = {2: "★★", 1: "★ ", 0: "· "}

SUMMARY_METRICS = ("hit_at_4", "ideal_at_4", "reciprocal_rank", "ndcg_at_12", "recall_at_12")
METRIC_LABELS = {
    "hit_at_4": "hit@4",
    "ideal_at_4": "ideal@4",
    "reciprocal_rank": "MRR",
    "ndcg_at_12": "nDCG@12",
    "recall_at_12": "recall@12",
}


def reciprocal_rank(grades: list[int]) -> float:
    """1 / rank of the first relevant item (grade > 0), 0.0 if there is none.
    `grades` holds the relevance grade of each ranked item, in rank order."""
    for index, grade in enumerate(grades):
        if grade > 0:
            return 1.0 / (index + 1)
    return 0.0


def hit_at_k(grades: list[int], k: int, min_grade: int = 1) -> bool:
    return any(grade >= min_grade for grade in grades[:k])


def recall_at_k(grades: list[int], relevant_count: int, k: int) -> float:
    if relevant_count == 0:
        return 0.0
    return sum(1 for grade in grades[:k] if grade > 0) / relevant_count


def _dcg(grades: list[int]) -> float:
    # Exponential gain: a grade-2 recipe is worth 3x a grade-1 one, so ranking
    # the actual vegetarian version first matters more than ranking "close".
    return sum((2**grade - 1) / math.log2(index + 2) for index, grade in enumerate(grades))


def ndcg_at_k(grades: list[int], judged_grades: list[int], k: int) -> float:
    """DCG of the top k, divided by the DCG of the best possible top k (every
    judged recipe, highest grade first). 0.0 when nothing is judged."""
    ideal = _dcg(sorted(judged_grades, reverse=True)[:k])
    if ideal == 0:
        return 0.0
    return _dcg(grades[:k]) / ideal


@dataclass
class QueryResult:
    id: str
    tags: list[str]
    first_relevant_rank: int | None
    reciprocal_rank: float
    hit_at_4: bool
    # None when the query has no grade-2 recipe to find.
    ideal_at_4: bool | None
    ndcg_at_12: float
    recall_at_12: float
    # Rank of every judged recipe (None when it isn't in the corpus at all).
    judged_ranks: dict[str, int | None]
    top_titles: list[str]


def grades_in_rank_order(ranked_titles: list[str], relevant: dict[str, int]) -> list[int]:
    """Grade of each ranked title. A judged title appearing twice (duplicate
    rows in the table) is only credited the first time, so duplicates can't
    inflate recall or nDCG."""
    seen: set[str] = set()
    grades = []
    for title in ranked_titles:
        grade = relevant.get(title, 0) if title not in seen else 0
        seen.add(title)
        grades.append(grade)
    return grades


def evaluate_ranking(
    query_id: str, tags: list[str], ranked_titles: list[str], relevant: dict[str, int]
) -> QueryResult:
    grades = grades_in_rank_order(ranked_titles, relevant)
    first_relevant = next((index + 1 for index, grade in enumerate(grades) if grade > 0), None)
    has_ideal = IDEAL_GRADE in relevant.values()
    return QueryResult(
        id=query_id,
        tags=tags,
        first_relevant_rank=first_relevant,
        reciprocal_rank=reciprocal_rank(grades),
        hit_at_4=hit_at_k(grades, FIRST_SCREEN),
        ideal_at_4=hit_at_k(grades, FIRST_SCREEN, min_grade=IDEAL_GRADE) if has_ideal else None,
        ndcg_at_12=ndcg_at_k(grades, list(relevant.values()), PAGE_SIZE),
        recall_at_12=recall_at_k(grades, len(relevant), PAGE_SIZE),
        judged_ranks={
            title: ranked_titles.index(title) + 1 if title in ranked_titles else None
            for title in relevant
        },
        top_titles=ranked_titles[:PAGE_SIZE],
    )


def summarize(results: list[QueryResult]) -> dict[str, float]:
    """Mean of every metric; booleans count as 1/0, and a metric that doesn't
    apply to a query (ideal_at_4 = None) is left out of that metric's mean."""
    summary = {}
    for metric in SUMMARY_METRICS:
        values = [getattr(result, metric) for result in results]
        values = [float(value) for value in values if value is not None]
        summary[metric] = mean(values) if values else 0.0
    return summary


def load_queries(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["queries"]


def rank_queries(queries: list[dict], recipes: list[Recipe]) -> list[QueryResult]:
    candidates = [recipe_service.build_candidate(recipe) for recipe in recipes]
    titles_by_id = {recipe.id: recipe.title for recipe in recipes}
    title_embeddings: dict[str, list[float]] = {}
    results = []
    for query in queries:
        if query["title"] not in title_embeddings:
            title_embeddings[query["title"]] = embed_text(query["title"])
        ranked = rank_candidates(
            title_embeddings[query["title"]],
            query["ingredients"],
            candidates,
            top_k=len(candidates),
        )
        ranked_titles = [titles_by_id[recipe_id] for recipe_id, _ in ranked]
        results.append(
            evaluate_ranking(query["id"], query["tags"], ranked_titles, query["relevant"])
        )
    return results


def _format_rank(rank: int | None) -> str:
    return "—" if rank is None else str(rank)


def report_queries(results: list[QueryResult], queries: list[dict], verbose: bool) -> None:
    logger.info(
        "%-26s %8s %6s %6s %8s %9s", "requête", "1er pert.", "RR", "hit@4", "nDCG@12", "recall@12"
    )
    relevant_by_id = {query["id"]: query["relevant"] for query in queries}
    for result in results:
        logger.info(
            "%-26s %8s %6.2f %6s %8.2f %9.2f",
            result.id,
            _format_rank(result.first_relevant_rank),
            result.reciprocal_rank,
            "oui" if result.hit_at_4 else "non",
            result.ndcg_at_12,
            result.recall_at_12,
        )
        if verbose:
            relevant = relevant_by_id[result.id]
            for title in result.top_titles[:FIRST_SCREEN]:
                logger.info("      %s %s", GRADE_MARKS[relevant.get(title, 0)], title)
            for title, rank in result.judged_ranks.items():
                if relevant[title] == IDEAL_GRADE and (rank is None or rank > FIRST_SCREEN):
                    logger.info("      attendu ★★ %s -> rang %s", title, _format_rank(rank))


def report_summary(results: list[QueryResult]) -> None:
    summary = summarize(results)
    logger.info("")
    logger.info(
        "Moyenne sur %d requêtes : %s",
        len(results),
        "  ".join(f"{METRIC_LABELS[metric]} {summary[metric]:.3f}" for metric in SUMMARY_METRICS),
    )
    tags = sorted({tag for result in results for tag in result.tags})
    logger.info("")
    logger.info("%-16s %4s %7s %7s %8s", "tag", "n", "hit@4", "MRR", "nDCG@12")
    for tag in tags:
        tagged = [result for result in results if tag in result.tags]
        tag_summary = summarize(tagged)
        logger.info(
            "%-16s %4d %7.2f %7.2f %8.2f",
            tag,
            len(tagged),
            tag_summary["hit_at_4"],
            tag_summary["reciprocal_rank"],
            tag_summary["ndcg_at_12"],
        )


def report_comparison(results: list[QueryResult], baseline_path: Path) -> None:
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    before = baseline["summary"]
    after = summarize(results)
    logger.info("")
    logger.info("Comparaison avec %s :", baseline_path)
    for metric in SUMMARY_METRICS:
        logger.info(
            "  %-10s %.3f -> %.3f  (%+.3f)",
            METRIC_LABELS[metric],
            before[metric],
            after[metric],
            after[metric] - before[metric],
        )

    previous = {query["id"]: query for query in baseline["queries"]}
    changed = [
        (result, previous[result.id])
        for result in results
        if result.id in previous
        and (
            result.first_relevant_rank != previous[result.id]["first_relevant_rank"]
            or abs(result.ndcg_at_12 - previous[result.id]["ndcg_at_12"]) > 1e-9
        )
    ]
    changed.sort(key=lambda pair: pair[0].ndcg_at_12 - pair[1]["ndcg_at_12"])
    logger.info("")
    logger.info("%d requête(s) modifiée(s) (nDCG@12 avant -> après, 1er pertinent) :", len(changed))
    for result, old in changed:
        logger.info(
            "  %-26s %.2f -> %.2f  (%+.2f)   rang %s -> %s",
            result.id,
            old["ndcg_at_12"],
            result.ndcg_at_12,
            result.ndcg_at_12 - old["ndcg_at_12"],
            _format_rank(old["first_relevant_rank"]),
            _format_rank(result.first_relevant_rank),
        )


def main() -> int:
    # Windows consoles default to a legacy code page when output is piped;
    # recipe titles are full of accents.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--queries", type=Path, default=DEFAULT_QUERIES_PATH)
    parser.add_argument(
        "--query", action="append", dest="query_ids", help="only this query id (repeatable)"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="show each query's first 4 suggestions"
    )
    parser.add_argument("--save", type=Path, help="write this run's results to a JSON file")
    parser.add_argument("--compare", type=Path, help="compare with a run saved by --save")
    args = parser.parse_args()

    queries = load_queries(args.queries)
    if args.query_ids:
        unknown = set(args.query_ids) - {query["id"] for query in queries}
        if unknown:
            logger.error("requête(s) inconnue(s) : %s", ", ".join(sorted(unknown)))
            return 1
        queries = [query for query in queries if query["id"] in args.query_ids]

    db = SessionLocal()
    try:
        recipes = list(db.execute(select(Recipe)).scalars().all())
    finally:
        db.close()

    # A judged title missing from the table would silently score as "never
    # suggested" — most likely a typo or a renamed recipe, so stop instead.
    corpus_titles = {recipe.title for recipe in recipes}
    missing = sorted(
        {title for query in queries for title in query["relevant"]} - corpus_titles
    )
    if missing:
        logger.error("%d recette(s) jugée(s) absente(s) de la base :", len(missing))
        for title in missing:
            logger.error("  %s", title)
        return 1

    logger.info("%d requête(s) classée(s) parmi %d recettes.", len(queries), len(recipes))
    logger.info("")
    results = rank_queries(queries, recipes)
    report_queries(results, queries, args.verbose)
    report_summary(results)

    if args.compare:
        report_comparison(results, args.compare)
    if args.save:
        args.save.write_text(
            json.dumps(
                {
                    "queries": [asdict(result) for result in results],
                    "summary": summarize(results),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        logger.info("")
        logger.info("Résultats enregistrés dans %s", args.save)
    return 0


if __name__ == "__main__":
    sys.exit(main())
