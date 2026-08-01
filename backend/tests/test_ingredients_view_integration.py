"""Sanity check against the real (gitignored) FlavorGraph data files —
skipped wherever they aren't present. See test_flavorgraph_integration.py.
"""

import pytest

from veggie_app.config import settings
from veggie_app.matching.ingredients_view import ingredients_view_score

_DATA_FILES_PRESENT = (settings.flavorgraph_dir / "embeddings.pickle").exists() and (
    settings.flavorgraph_dir / "nodes.csv"
).exists()

pytestmark = pytest.mark.skipif(
    not _DATA_FILES_PRESENT,
    reason="FlavorGraph data files not present (see backend/data/flavorgraph/README.md)",
)


def test_scores_higher_for_a_closer_match() -> None:
    # Query describes a beef + onion + carrot dish; "seitan" is a much closer
    # substitute for "boeuf" (0.90) than "champignon" is unrelated-ish here,
    # and the non-protein ingredients match exactly on the seitan candidate.
    close_match = ingredients_view_score(
        query_ingredients=["boeuf", "oignon", "carotte"],
        candidate_ingredients=["seitan", "oignon", "carotte"],
        candidate_protein_source="seitan",
    )
    far_match = ingredients_view_score(
        query_ingredients=["boeuf", "oignon", "carotte"],
        candidate_ingredients=["tomate", "basilic"],
        candidate_protein_source=None,
    )

    assert close_match > far_match


def test_falls_back_to_rest_score_with_no_protein_anywhere() -> None:
    score = ingredients_view_score(
        query_ingredients=["oignon", "carotte"],
        candidate_ingredients=["carotte", "oignon"],
        candidate_protein_source=None,
    )

    assert score == pytest.approx(1.0, abs=1e-4)
