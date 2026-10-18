"""The "Structure view": compares what *kind* of dish two recipes are — their
dish types (a stew, a gratin, a curry, a pasta dish...) and their cuisine —
rather than their title wording or their ingredients. A bœuf bourguignon and
a seitan bourguignon share a form and a tradition even where their proteins
and half their ingredients differ; this view is what lets that count.

Recipes carry curated tags (Recipe.dish_types / Recipe.cuisine, validated
against DISH_TYPES / CUISINES). A query is only a dish name typed by a user,
so its tags are inferred from the title with DISH_LEXICON
(matching/dish_lexicon.py). When either side has no tag the view has nothing
to say and is skipped, so untagged recipes and unknown dishes rank exactly as
they did before this view existed.

Pure functions only — no FastAPI or DB dependency — like the rest of matching/.
See docs/ARCHITECTURE.md "Dish structure view".
"""

from collections.abc import Sequence
from dataclasses import dataclass
from functools import lru_cache

from veggie_app.matching.dish_lexicon import DISH_LEXICON
from veggie_app.matching.ingredient_names import canonical_name

# What form the dish takes. A recipe may have several ("lasagnes" are both a
# gratin and a pasta dish); two recipes match on this axis when they share one.
DISH_TYPES: tuple[str, ...] = (
    "boulettes",
    "chausson",
    "curry",
    "farci",
    "galette",
    "gratin",
    "nouilles",
    "pané-frit",
    "pâtes",
    "purée",
    "ragoût",
    "riz",
    "rôti-grillé",
    "salade",
    "sandwich",
    "sauté",
    "soupe",
    "tacos",
    "tarte",
    "terrine",
    "œufs",
)

# Cuisine -> region. Same cuisine is a full match, same region a partial one
# (a Thai curry for a Vietnamese dish is closer than an Italian one).
CUISINE_REGIONS: dict[str, str] = {
    "française": "europe",
    "italienne": "europe",
    "espagnole": "europe",
    "grecque": "europe",
    "europe centrale et de l'est": "europe",
    "europe du nord": "europe",
    "maghrébine": "afrique et moyen-orient",
    "moyen-orientale": "afrique et moyen-orient",
    "africaine": "afrique et moyen-orient",
    "indienne": "asie du sud et du sud-est",
    "asie du sud-est": "asie du sud et du sud-est",
    "chinoise": "asie de l'est",
    "japonaise": "asie de l'est",
    "coréenne": "asie de l'est",
    "mexicaine": "amériques",
    "nord-américaine": "amériques",
    "latino-américaine et caribéenne": "amériques",
}
CUISINES: tuple[str, ...] = tuple(sorted(CUISINE_REGIONS))

# Within the view: what the dish *is* weighs more than where it comes from.
DISH_TYPE_SHARE = 0.6
SAME_REGION_SCORE = 0.5


@dataclass(frozen=True)
class DishStructure:
    dish_types: frozenset[str] = frozenset()
    cuisine: str | None = None

    @property
    def is_empty(self) -> bool:
        return not self.dish_types and self.cuisine is None


NO_STRUCTURE = DishStructure()


@lru_cache(maxsize=1)
def _lexicon_index() -> list[tuple[list[str], frozenset[str], str | None]]:
    """DISH_LEXICON keyed by canonical words, longest phrase first so
    "tortilla espagnole" is read before "tortilla"."""
    entries = [
        (canonical_name(phrase).split(), frozenset(dish_types), cuisine)
        for phrase, (dish_types, cuisine) in DISH_LEXICON.items()
    ]
    return sorted(entries, key=lambda entry: -len(entry[0]))


@lru_cache(maxsize=4096)
def infer_dish_structure(title: str) -> DishStructure:
    """Dish types and cuisine of a dish *name*, from the lexicon: every
    phrase found in the title adds its dish types; the cuisine comes from the
    longest phrase that names one. Words already used by a longer phrase
    aren't read again ("tortilla espagnole" is an omelette, not a tacos)."""
    words = canonical_name(title).split()
    used = [False] * len(words)
    dish_types: set[str] = set()
    cuisine: str | None = None
    for phrase, phrase_types, phrase_cuisine in _lexicon_index():
        size = len(phrase)
        for start in range(len(words) - size + 1):
            if words[start : start + size] == phrase and not any(used[start : start + size]):
                used[start : start + size] = [True] * size
                dish_types |= phrase_types
                if cuisine is None:
                    cuisine = phrase_cuisine
    return DishStructure(dish_types=frozenset(dish_types), cuisine=cuisine)


def _cuisine_score(query_cuisine: str, candidate_cuisine: str) -> float:
    if query_cuisine == candidate_cuisine:
        return 1.0
    if CUISINE_REGIONS.get(query_cuisine) == CUISINE_REGIONS.get(candidate_cuisine):
        return SAME_REGION_SCORE
    return 0.0


def structure_score(
    query: DishStructure, candidate_dish_types: Sequence[str], candidate_cuisine: str | None
) -> float | None:
    """How alike the two dishes are in form and tradition, in [0, 1], or None
    when there's nothing to compare (no axis tagged on both sides). Dish types
    match when the two share one; when only one axis can be compared, it
    carries the whole score."""
    dish_score = (
        float(bool(query.dish_types & set(candidate_dish_types)))
        if query.dish_types and candidate_dish_types
        else None
    )
    cuisine_score = (
        _cuisine_score(query.cuisine, candidate_cuisine)
        if query.cuisine and candidate_cuisine
        else None
    )
    if dish_score is None and cuisine_score is None:
        return None
    if cuisine_score is None:
        return dish_score
    if dish_score is None:
        return cuisine_score
    return DISH_TYPE_SHARE * dish_score + (1 - DISH_TYPE_SHARE) * cuisine_score
