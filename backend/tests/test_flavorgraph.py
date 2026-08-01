import numpy as np
import pytest

from veggie_app.matching import flavorgraph
from veggie_app.matching.flavorgraph import FlavorGraphDataError, get_vector

FAKE_MAPPING = {"oignon": "onion", "carotte": "carrot"}
FAKE_NAME_TO_ID = {"onion": "101", "carrot": "202"}
FAKE_EMBEDDINGS = {
    "101": np.array([1.0, 0.0, 0.0]),
    "202": np.array([0.0, 1.0, 0.0]),
}


@pytest.fixture(autouse=True)
def _stub_flavorgraph_data(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test in this file uses a tiny in-memory fixture instead of the
    real (gitignored, ~10MB) FlavorGraph data files."""
    monkeypatch.setattr(flavorgraph, "_load_embeddings", lambda: FAKE_EMBEDDINGS)
    monkeypatch.setattr(flavorgraph, "_load_ingredient_name_to_id", lambda: FAKE_NAME_TO_ID)


def test_get_vector_resolves_mapped_ingredient() -> None:
    vector = get_vector("oignon", mapping=FAKE_MAPPING)

    assert vector is not None
    assert list(vector) == [1.0, 0.0, 0.0]


def test_get_vector_is_case_insensitive() -> None:
    vector = get_vector("Oignon", mapping=FAKE_MAPPING)

    assert vector is not None
    assert list(vector) == [1.0, 0.0, 0.0]


def test_get_vector_returns_none_for_unmapped_ingredient() -> None:
    assert get_vector("courgette", mapping=FAKE_MAPPING) is None


def test_get_vector_returns_none_when_mapped_name_missing_from_vocabulary() -> None:
    mapping = {"poireau": "leek"}  # "leek" isn't in FAKE_NAME_TO_ID

    assert get_vector("poireau", mapping=mapping) is None


def test_get_vector_returns_none_when_node_id_missing_from_embeddings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        flavorgraph, "_load_ingredient_name_to_id", lambda: {"onion": "not-in-embeddings"}
    )

    assert get_vector("oignon", mapping=FAKE_MAPPING) is None


def test_get_vector_degrades_gracefully_when_data_files_are_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression guard: the FlavorGraph data files are a manually-downloaded,
    gitignored asset — absent in CI and on a fresh clone. Their absence must
    degrade the ingredients view, not crash every suggestion request."""

    def _raise() -> dict:
        raise FlavorGraphDataError("fichier introuvable (test)")

    monkeypatch.setattr(flavorgraph, "_load_ingredient_name_to_id", _raise)

    assert get_vector("oignon", mapping=FAKE_MAPPING) is None


def test_get_vector_uses_default_source_to_flavorgraph_mapping() -> None:
    """Called without an explicit mapping, falls back to the module's own
    SOURCE_TO_FLAVORGRAPH ("oignon" -> "onion") — sanity check that the
    default wiring works, not just the injected-mapping path exercised by
    the other tests."""
    vector = get_vector("oignon")

    assert vector is not None
    assert list(vector) == [1.0, 0.0, 0.0]
