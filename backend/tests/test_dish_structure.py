import pytest

from veggie_app.matching.dish_lexicon import DISH_LEXICON
from veggie_app.matching.dish_structure import (
    CUISINE_REGIONS,
    CUISINES,
    DISH_TYPE_SHARE,
    DISH_TYPES,
    NO_STRUCTURE,
    SAME_REGION_SCORE,
    DishStructure,
    infer_dish_structure,
    structure_score,
)


def test_lexicon_only_uses_known_dish_types_and_cuisines() -> None:
    for phrase, (dish_types, cuisine) in DISH_LEXICON.items():
        assert set(dish_types) <= set(DISH_TYPES), phrase
        assert cuisine is None or cuisine in CUISINES, phrase


def test_every_cuisine_has_a_region() -> None:
    assert set(CUISINES) == set(CUISINE_REGIONS)


@pytest.mark.parametrize(
    ("title", "dish_types", "cuisine"),
    [
        ("Bœuf bourguignon", {"ragoût"}, "française"),
        ("Lasagnes à la bolognaise", {"gratin", "pâtes"}, "italienne"),
        ("Poulet tikka masala", {"curry"}, "indienne"),
        ("Pad thaï aux crevettes", {"nouilles"}, "asie du sud-est"),
        ("Chili con carne", {"ragoût"}, "mexicaine"),
    ],
)
def test_infer_dish_structure_reads_known_dishes(
    title: str, dish_types: set[str], cuisine: str
) -> None:
    assert infer_dish_structure(title) == DishStructure(frozenset(dish_types), cuisine)


def test_infer_dish_structure_reads_a_longer_phrase_before_its_words() -> None:
    # An omelette, not a tacos: "tortilla espagnole" wins over "tortilla".
    assert infer_dish_structure("Tortilla espagnole aux oignons").dish_types == {"œufs"}


def test_infer_dish_structure_combines_a_dish_word_and_a_cuisine_word() -> None:
    structure = infer_dish_structure("Curry de légumes à la thaïlandaise")

    assert structure == DishStructure(frozenset({"curry"}), "asie du sud-est")


def test_infer_dish_structure_gives_no_cuisine_for_an_ambiguous_dish() -> None:
    # Indian, Thai and Japanese curries all exist.
    assert infer_dish_structure("Poulet au curry").cuisine is None


def test_infer_dish_structure_of_an_unknown_name_is_empty() -> None:
    assert infer_dish_structure("Recette de grand-mère").is_empty


def test_structure_score_full_match() -> None:
    query = DishStructure(frozenset({"ragoût"}), "française")

    assert structure_score(query, ["ragoût"], "française") == pytest.approx(1.0)


def test_structure_score_shares_one_dish_type_out_of_several() -> None:
    query = DishStructure(frozenset({"gratin", "pâtes"}), None)

    assert structure_score(query, ["pâtes"], None) == 1.0


def test_structure_score_same_region_counts_half() -> None:
    query = DishStructure(frozenset({"curry"}), "asie du sud-est")

    expected = DISH_TYPE_SHARE * 1.0 + (1 - DISH_TYPE_SHARE) * SAME_REGION_SCORE
    assert structure_score(query, ["curry"], "indienne") == pytest.approx(expected)


def test_structure_score_different_dish_and_cuisine_is_zero() -> None:
    query = DishStructure(frozenset({"ragoût"}), "française")

    assert structure_score(query, ["salade"], "japonaise") == 0.0


def test_structure_score_uses_the_only_comparable_axis() -> None:
    query = DishStructure(frozenset({"ragoût"}), "française")

    assert structure_score(query, ["ragoût"], None) == 1.0  # recipe has no cuisine
    assert structure_score(query, [], "française") == 1.0  # recipe has no dish type


def test_structure_score_is_none_when_nothing_can_be_compared() -> None:
    assert structure_score(NO_STRUCTURE, ["ragoût"], "française") is None
    assert structure_score(DishStructure(frozenset({"ragoût"}), None), [], "française") is None
