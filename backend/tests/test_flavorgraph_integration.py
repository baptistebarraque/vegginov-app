"""Sanity check against the real (gitignored) FlavorGraph data files —
skipped wherever they aren't present (CI, a fresh clone before download).
Everything else about flavorgraph.py is covered, without the real files, in
test_flavorgraph.py.
"""

import pytest

from veggie_app.config import settings
from veggie_app.matching import flavorgraph
from veggie_app.matching.flavorgraph import get_vector

_DATA_FILES_PRESENT = (settings.flavorgraph_dir / "embeddings.pickle").exists() and (
    settings.flavorgraph_dir / "nodes.csv"
).exists()

pytestmark = pytest.mark.skipif(
    not _DATA_FILES_PRESENT,
    reason="FlavorGraph data files not present (see backend/data/flavorgraph/README.md)",
)


def test_get_vector_resolves_a_real_mapped_ingredient() -> None:
    vector = get_vector("oignon")

    assert vector is not None
    assert len(vector) == 300


def test_get_vector_returns_none_for_an_unmapped_ingredient() -> None:
    assert get_vector("un-ingredient-totalement-invente-xyz") is None


def test_every_vocabulary_entry_points_at_a_real_ingredient_node() -> None:
    known = flavorgraph._load_ingredient_name_to_id()

    missing = {
        key: concept
        for key, concept in flavorgraph.SOURCE_TO_FLAVORGRAPH.items()
        if concept not in known
    }

    assert missing == {}
