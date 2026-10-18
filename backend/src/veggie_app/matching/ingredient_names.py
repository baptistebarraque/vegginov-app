"""Spelling-insensitive ingredient names: one canonical form shared by every
vocabulary lookup (FlavorGraph map, protein vocabulary) and by whatever a user
or a recipe actually wrote.

A miss in those lookups is silent — the ingredient is simply dropped from
similarity scoring — so every spelling difference that doesn't change the
meaning is erased here, on both sides of the lookup at once: case, accents,
ligatures ("bœuf"), apostrophes and hyphens, a leading quantity ("200 g de"),
and plurals ("tomates"). See docs/ARCHITECTURE.md "Query recognition".

Pure functions only — no FastAPI or DB dependency — like the rest of matching/.
"""

import re
import unicodedata
from functools import lru_cache

# Small words that link a head noun to its complement ("blanc *de* poulet").
# A shortened name never ends on one of them.
CONNECTOR_WORDS = frozenset(
    {"a", "au", "aux", "d'", "de", "des", "du", "en", "et", "l'", "la", "le"}
)

_LIGATURES = str.maketrans({"œ": "oe", "æ": "ae", "’": "'", "‘": "'", "-": " "})

# A leading quantity: "200g", "2", "1/2", "1,5 kg", "3 c. a soupe", optionally
# followed by "de"/"d'". Only stripped from the start of a name.
_UNITS = (
    r"(?:kg|g|mg|l|dl|cl|ml|cs|cc"
    r"|c\.?\s*a\s*(?:soupe|cafe)s?|cuilleres?\s*a\s*(?:soupe|cafe)s?)"
)
_LEADING_QUANTITY = re.compile(rf"^\d+(?:[.,/]\d+)?\s*(?:{_UNITS}\b\.?)?\s*(?:(?:de|d')\s+)?")

# Below this length a word is left alone when singularizing ("os", "riz").
_MIN_PLURAL_LENGTH = 4


def _singular(word: str) -> str:
    """French plural -> singular for the regular cases. Applied identically to
    both sides of every lookup, so the irregular cases it mangles ("pois" ->
    "poi") still match each other; only the result's consistency matters."""
    if len(word) < _MIN_PLURAL_LENGTH or word in CONNECTOR_WORDS:
        return word
    if word.endswith("eaux"):
        return word[:-1]  # poireaux -> poireau
    if word.endswith("oux"):
        return word[:-1]  # choux -> chou
    if word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


@lru_cache(maxsize=65536)
def canonical_name(text: str) -> str:
    """Canonical form of an ingredient name: "Bœufs hachés" -> "boeuf hache",
    "200 g de Tomates" -> "tomate", "pain d'épices" -> "pain d' epice".
    Cached because it runs on every ingredient of every candidate recipe."""
    text = text.lower().translate(_LIGATURES)
    text = "".join(
        character
        for character in unicodedata.normalize("NFD", text)
        if unicodedata.category(character) != "Mn"
    )
    # "d'agneau" -> "d' agneau", so the noun after an elided article is a word
    # of its own and can be matched like any other.
    text = text.replace("'", "' ")
    text = " ".join(text.split())
    text = _LEADING_QUANTITY.sub("", text)
    return " ".join(_singular(word) for word in text.split())


def shortened_forms(canonical: str) -> list[str]:
    """The canonical name, then each shorter version obtained by dropping
    trailing words — longest first, never ending on a connector word:
    "champignon de pari" -> ["champignon de pari", "champignon"]. French
    puts the head noun first and its modifiers after, so dropping from the
    end walks back to the noun a vocabulary is most likely to know."""
    words = canonical.split()
    forms = []
    for length in range(len(words), 0, -1):
        if words[length - 1] in CONNECTOR_WORDS:
            continue
        forms.append(" ".join(words[:length]))
    return forms
