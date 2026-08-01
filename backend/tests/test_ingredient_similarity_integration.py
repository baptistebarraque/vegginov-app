"""Sanity check against the real (gitignored) FlavorGraph data files —
skipped wherever they aren't present. See test_flavorgraph_integration.py.
"""

import pytest

from veggie_app.config import settings
from veggie_app.matching.ingredient_similarity import ingredient_set_similarity

_DATA_FILES_PRESENT = (settings.flavorgraph_dir / "embeddings.pickle").exists() and (
    settings.flavorgraph_dir / "nodes.csv"
).exists()

pytestmark = pytest.mark.skipif(
    not _DATA_FILES_PRESENT,
    reason="FlavorGraph data files not present (see backend/data/flavorgraph/README.md)",
)


def test_identical_ingredient_sets_score_near_one() -> None:
    score = ingredient_set_similarity(["oignon", "carotte"], ["carotte", "oignon"])

    assert score == pytest.approx(1.0, abs=1e-4)


def test_unrelated_and_unmapped_ingredients_score_lower() -> None:
    identical_score = ingredient_set_similarity(["oignon"], ["oignon"])
    unrelated_score = ingredient_set_similarity(["oignon"], ["champignon"])

    assert unrelated_score < identical_score
