import numpy as np
import pytest

from veggie_app.matching import flavorgraph
from veggie_app.matching.flavorgraph import FlavorGraphDataError, get_vector
from veggie_app.matching.ingredient_names import canonical_name

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


def test_get_vector_ignores_missing_accents() -> None:
    """The map spells it "épinards"; a recipe may well spell it "epinards".
    That used to resolve to None and silently drop the ingredient out of
    similarity scoring — the failure this whole normalization exists to stop."""
    monkeypatched = {"épinards": "onion"}

    assert get_vector("epinards", mapping=monkeypatched) is not None


def test_get_vector_ignores_spurious_accents() -> None:
    """The reverse direction: an accent the map doesn't have must not break
    the lookup either, so neither side is the "correct" spelling."""
    monkeypatched = {"quinoa": "onion"}

    assert get_vector("quínoa", mapping=monkeypatched) is not None


def test_get_vector_matches_accented_default_vocabulary_without_accents() -> None:
    """End-to-end on the real SOURCE_TO_FLAVORGRAPH rather than a fixture:
    the map spells this entry "oignon émincé", and the unaccented spelling has
    to reach the same vector. (This key is used because it carries accents
    *and* resolves to one of the stubbed concepts above.)"""
    accented = get_vector("oignon émincé")
    unaccented = get_vector("oignon emince")

    assert accented is not None
    assert unaccented is not None
    assert list(accented) == list(unaccented)


def test_canonicalizing_the_vocabulary_loses_no_distinct_concept() -> None:
    """Guard on the assumption `_canonical_source_to_flavorgraph` is built on:
    collapsing keys by canonical form (accents, plurals, quantities) must never
    merge two entries that point at different FlavorGraph concepts, or one of
    them would become unreachable. Adding such a pair to the map should fail
    here, not silently mis-rank."""
    by_canonical: dict[str, set[str]] = {}
    for key, concept in flavorgraph.SOURCE_TO_FLAVORGRAPH.items():
        by_canonical.setdefault(canonical_name(key), set()).add(concept)

    collisions = {key: concepts for key, concepts in by_canonical.items() if len(concepts) > 1}

    assert collisions == {}


def test_get_vector_matches_plurals_and_ligatures() -> None:
    mapping = {"oignon": "onion", "bœuf": "carrot"}

    assert get_vector("oignons", mapping=mapping) is not None
    assert get_vector("boeufs", mapping=mapping) is not None


def test_get_vector_falls_back_to_the_head_noun() -> None:
    vector = get_vector("oignons rouges émincés", mapping=FAKE_MAPPING)

    assert vector is not None
    assert list(vector) == [1.0, 0.0, 0.0]


def test_get_vector_prefers_the_longest_known_form() -> None:
    mapping = {"oignon": "onion", "oignon rouge": "carrot"}

    vector = get_vector("oignons rouges émincés", mapping=mapping)

    assert vector is not None
    assert list(vector) == [0.0, 1.0, 0.0]  # "oignon rouge", not "oignon"


@pytest.mark.parametrize(
    ("written", "concept"),
    [
        # Compounds whose meaning is the complement, not the head noun: they
        # must be keys of their own, or the head-noun fallback would resolve
        # them to the wrong ingredient (walnut, butter, pasta, milk...).
        ("noix de coco", "coconut"),
        ("beurre de cacahuète", "peanut_butter"),
        ("lait de coco", "coconut_milk"),
        ("pâte à pain", "bread_dough"),
        ("pâtes à lasagne", "lasagna_noodle"),
        ("pommes de terre nouvelles", "potato"),
        ("noix de muscade", "nutmeg"),
        ("crème de coco", "coconut_milk"),
    ],
)
def test_real_vocabulary_resolves_compounds_to_the_right_concept(
    written: str, concept: str
) -> None:
    assert flavorgraph._lookup(written, flavorgraph._canonical_source_to_flavorgraph()) == concept
