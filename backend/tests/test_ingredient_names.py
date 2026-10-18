import pytest

from veggie_app.matching.ingredient_names import canonical_name, shortened_forms


@pytest.mark.parametrize(
    ("written", "canonical"),
    [
        ("Épinards", "epinard"),
        ("bœuf", "boeuf"),
        ("Bœufs Hachés", "boeuf hache"),
        ("tomates", "tomate"),
        ("poireaux", "poireau"),
        ("choux", "chou"),
        ("pain d’épices", "pain d' epice"),
        ("épaule d'agneau", "epaule d' agneau"),
        ("chou-fleur", "chou fleur"),
        ("  oignon   rouge ", "oignon rouge"),
    ],
)
def test_canonical_name_erases_spelling_differences(written: str, canonical: str) -> None:
    assert canonical_name(written) == canonical


@pytest.mark.parametrize(
    "written",
    [
        "200g de tomates",
        "200 g de tomates",
        "2 tomates",
        "1,5 kg de tomates",
        "3 c. à soupe de tomates",
    ],
)
def test_canonical_name_strips_a_leading_quantity(written: str) -> None:
    assert canonical_name(written) == "tomate"


def test_canonical_name_strips_quantity_before_elided_article() -> None:
    assert canonical_name("1 gousse d'ail") == "gousse d' ail"


def test_canonical_name_keeps_short_words_and_double_s() -> None:
    # Too short to be a regular plural, or not a plural at all.
    assert canonical_name("os") == "os"
    assert canonical_name("riz") == "riz"
    assert canonical_name("cresson") == "cresson"


def test_canonical_name_is_identical_for_singular_and_plural_of_irregular_words() -> None:
    # "pois" is mangled to "poi", but identically on both sides of a lookup,
    # which is all that matters.
    assert canonical_name("pois chiches") == canonical_name("pois chiche")


def test_shortened_forms_go_from_longest_to_head_noun() -> None:
    assert shortened_forms("tomate concassee fraiche") == [
        "tomate concassee fraiche",
        "tomate concassee",
        "tomate",
    ]


def test_shortened_forms_never_end_on_a_connector_word() -> None:
    assert shortened_forms(canonical_name("champignons de Paris")) == [
        "champignon de pari",
        "champignon",
    ]
    assert shortened_forms(canonical_name("épaule d'agneau")) == ["epaule d' agneau", "epaule"]


def test_shortened_forms_of_a_single_word() -> None:
    assert shortened_forms("tomate") == ["tomate"]
