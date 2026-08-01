"""FlavorGraph ingredient-embedding lookup (see backend/data/flavorgraph/README.md
for the data files this reads and where to get them).

FlavorGraph's embeddings are keyed by an internal node_id, and its vocabulary
is English — so looking up an ingredient from the app's own (French) data
takes two steps: translate via SOURCE_TO_FLAVORGRAPH, then resolve that
English name to a node_id via nodes.csv, then to a vector via the pickle.

Loading is lazy and cached (same reasoning as embeddings.py's
_get_model(): most tests never need the real ~10MB data files, only this
module's pure functions with a fake vocabulary/embeddings dict injected).
"""

import csv
import logging
import pickle
from functools import lru_cache

import numpy as np

from veggie_app.config import settings

logger = logging.getLogger(__name__)

EMBEDDINGS_FILENAME = "embeddings.pickle"
NODES_FILENAME = "nodes.csv"
INGREDIENT_NODE_TYPE = "ingredient"

# Source-language (French) -> FlavorGraph English vocabulary. Keys are exact
# ingredient strings (get_vector lowercases before lookup, no other
# normalization) — as messy/descriptive as the recipe database's actual
# `ingredients[].name` values ("carottes coupées en dés", not just
# "carotte"), since that's what's actually looked up at query/candidate
# time. Every value below was checked against the real nodes.csv (only
# `ingredient`-typed rows) before being added. Expand this as the database's
# vocabulary grows (see docs design notes, section 5.2) — a new ingredient
# phrase with no matching key here just means get_vector returns None for
# it (logged, not fatal).
SOURCE_TO_FLAVORGRAPH: dict[str, str] = {
    # --- Aromatics / alliums ---
    "ail": "garlic",
    "1 gousse d'ail": "garlic",
    "gousse d'ail": "garlic",
    "gousses d'ail": "garlic",
    "gousses d'ail émincées": "garlic",
    "gousses d'ail hachées": "garlic",
    "oignon": "onion",
    "1 oignon": "onion",
    "oignons": "onion",
    "oignon émincé": "onion",
    "oignon rouge émincé": "onion",
    "oignons émincés": "onion",
    "oignons nouveaux émincés": "onion",
    "echalotte": "shallot",
    # --- Vegetables ---
    "carotte en bâtonnets": "carrot",
    "carotte en julienne": "carrot",
    "carotte râpée": "carrot",
    "carottes coupées en dés": "carrot",
    "carottes coupées en rondelles": "carrot",
    "carottes en dés": "carrot",
    "carottes en rondelles": "carrot",
    "courgette": "zucchini",
    "courgette coupée en dés": "zucchini",
    "courgette en dés": "zucchini",
    "courgette en fines tranches": "zucchini",
    "courgettes coupées en dés": "zucchini",
    "courgettes coupées en rondelles": "zucchini",
    "courgettes en dés": "zucchini",
    "2 aubergines": "eggplant",
    "aubergine en cubes": "eggplant",
    "aubergine en dés": "eggplant",
    "aubergine en fines tranches": "eggplant",
    "aubergines coupées en dés": "eggplant",
    "chair de potiron en cubes": "pumpkin",
    "champignons": "mushroom",
    "champignons de paris émincés": "mushroom",
    "concombre": "cucumber",
    "concombre coupé en dés": "cucumber",
    "concombre en bâtonnets": "cucumber",
    "concombre en dés": "cucumber",
    "concombre en rondelles": "cucumber",
    "brocoli en bouquets": "broccoli",
    "chou-fleur en bouquets": "cauliflower",
    "chou-fleur en petits bouquets": "cauliflower",
    "branche de céleri": "celery",
    "branche de céleri en bâtonnets": "celery",
    "poireaux émincés": "leek",
    "épinards frais": "spinach",
    "jeunes pousses d'épinard": "spinach",
    "laitue romaine": "romaine_lettuce",
    "300g de pulpe de tomate en boîte": "tomato",
    "tomate": "tomato",
    "tomate coupée en dés": "tomato",
    "tomates cerises coupées en deux": "tomato",
    "tomates concassées": "tomato",
    "tomates coupées en dés": "tomato",
    "tomates coupées en quartiers": "tomato",
    "tomates en fines tranches": "tomato",
    "gros poivrons": "bell_pepper",
    "piment doux": "bell_pepper",
    "poivron coupé en dés": "bell_pepper",
    "poivron en dés": "bell_pepper",
    "poivron en lanières": "bell_pepper",
    "poivrons coupés en dés": "bell_pepper",
    "poivron rouge coupé en dés": "red_bell_pepper",
    "poivron rouge en dés": "red_bell_pepper",
    "piments jalapeño émincés": "canned_jalapeno_pepper",
    "olives noires": "black_olive",
    "maïs": "corn",
    "maïs en boîte": "corn",
    "pommes de terre en cubes": "potato",
    "pommes de terre en fines tranches": "potato",
    "patates douces coupées en cubes": "sweet_potato",
    "patates douces en cubes": "sweet_potato",
    "petits pois": "pea",
    # --- Fruits ---
    "avocat écrasé": "avocado",
    "avocat tranché": "avocado",
    "bananes": "banana",
    "bananes coupées en rondelles": "banana",
    "bananes mûres écrasées": "banana",
    "citron": "lemon",
    "citron vert": "lime",
    "fruits rouges surgelés": "mixed_berry",
    "4c à soupes de raisins secs": "raisin",
    # --- Legumes / grains / starches ---
    "200g de pois chiche": "chickpea",
    "farine de pois chiche": "chickpea",
    "pois chiches en boîte": "chickpea",
    "pois chiches secs trempés la veille": "chickpea",
    "pois chiches égouttés": "chickpea",
    "lentilles corail": "red_lentil",
    "lentilles vertes": "green_lentil",
    "haricots blancs en boîte": "white_bean",
    "haricots noirs en boîte": "black_bean",
    "haricots rouges en boîte": "kidney_bean",
    "haricots verts": "green_bean",
    "riz": "rice",
    "riz arborio": "arborio_rice",
    "riz cuit": "cooked_rice",
    "riz cuit (idéalement de la veille)": "cooked_rice",
    "riz cuit refroidi": "cooked_rice",
    "quinoa": "quinoa",
    "pâtes (penne ou spaghetti)": "pasta",
    "pâtes (tagliatelles ou fusilli)": "pasta",
    "pâtes courtes (fusilli ou farfalle)": "pasta",
    "nouilles de riz": "rice_noodle",
    "gnocchis": "gnocchi",
    "tortillas de blé": "flour_tortilla",
    "tortillas de maïs": "corn_tortilla",
    "pains à burger": "sandwich_bread",
    "tranches de pain": "bread",
    "tranches de pain de mie": "sandwich_bread",
    "pâte à pizza": "pizza_dough",
    "pâte brisée": "pie_crust",
    "plaques de lasagnes": "lasagna_noodle",
    # --- Proteins / dairy / eggs ---
    "tofu": "tofu",
    "tofu ferme coupé en cubes": "firm_tofu",
    "tofu ferme en dés": "firm_tofu",
    "tofu ferme en tranches": "firm_tofu",
    "tofu soyeux coupé en dés": "silken_tofu",
    "œuf": "egg",
    "œuf pour dorer": "egg",
    "œufs": "egg",
    "œufs battus": "egg",
    "lait": "milk",
    "20cl de lait ou crème coco": "coconut_milk",
    "lait de coco": "coconut_milk",
    "creme fraiche": "sour_cream",
    "crème fraîche": "sour_cream",
    "beurre": "butter",
    "fromage": "cheese",
    "fromage râpé": "cheese",
    "emmental râpé": "cheese",
    "mozzarella": "mozzarella_cheese",
    "mozzarella coupée en dés": "mozzarella_cheese",
    "mozzarella râpée": "mozzarella_cheese",
    "parmesan râpé": "parmesan_cheese",
    "gruyere": "gruyere_cheese",
    "gruyère râpé": "gruyere_cheese",
    "feta": "feta_cheese",
    "feta en cubes": "feta_cheese",
    "feta en dés": "feta_cheese",
    "feta émiettée": "feta_cheese",
    "chèvre": "goat_cheese",
    "yaourt grec": "greek_yogurt",
    # --- Herbs / spices / seasonings ---
    "basilic frais": "basil",
    "bouquet de basilic frais": "basil",
    "bouquet de basilic thaï": "basil",
    "pesto au basilic": "basil",
    "bouquet de coriandre": "cilantro",
    "coriandre fraîche": "cilantro",
    "persil et coriandre": "cilantro",
    "thym frais": "thyme",
    "origan": "oregano",
    "origan séché": "oregano",
    "feuille de laurier": "bay_leaf",
    "muscade": "nutmeg",
    "cumin": "cumin",
    "curcuma": "turmeric",
    "paprika": "paprika",
    "paprika fumé": "smoked_paprika",
    "gingembre râpé": "ginger",
    "garam masala": "garam_masala",
    "herbes de provence": "herbes_de_provence",
    "sel": "salt",
    "poivre": "black_pepper",
    "sucre": "sugar",
    # --- Sauces / condiments / oils / liquids ---
    "huile d'olive": "olive_oil",
    "huile de sésame": "sesame_oil",
    "vinaigre balsamique": "balsamic_vinegar",
    "vinaigre de riz": "rice_vinegar",
    "sauce soja": "soy_sauce",
    "sauce tomate": "tomato_sauce",
    "sauce césar": "caesar_salad_dressing",
    "curry": "curry_powder",
    "curry en poudre": "curry_powder",
    "pâte de curry": "curry_paste",
    "pâte de curry vert": "green_curry_paste",
    "houmous": "hummus",
    "tahini": "tahini",
    "pâte miso": "miso",
    "sirop d'érable": "maple_syrup",
    "2c à café de miel": "honey",
    "miel": "honey",
    "vin blanc": "white_wine",
    "vin rouge": "red_wine",
    "eau": "water",
    "15cl de bouillon de légumes": "vegetable_bouillon",
    "bouillon de légumes": "vegetable_bouillon",
    "bouillon de légumes chaud": "vegetable_bouillon",
    "levure chimique": "baking_powder",
    "farine": "all_purpose_flour",
    # --- Nuts / seeds / misc ---
    "amandes effilées": "sliced_almond",
    "cacahuètes concassées": "roasted_peanut",
    "noix concassées": "walnut",
    "pignons de pin": "pine_nut",
    "graines de chia": "chia_seed",
    "graines de sésame": "sesame_seed",
    "granola": "granola_cereal",
    "flocons d'avoine": "oatmeal",
    "chapelure": "seasoned_bread_crumb",
    "croûtons": "crouton",
    "pousses de soja": "bean_sprout",
    "feuille d'algue wakame réhydratée": "wakame_seaweed",
}


class FlavorGraphDataError(RuntimeError):
    """Raised when the FlavorGraph data files are missing or malformed."""


@lru_cache(maxsize=1)
def _load_embeddings() -> dict[str, np.ndarray]:
    path = settings.flavorgraph_dir / EMBEDDINGS_FILENAME
    if not path.exists():
        raise FlavorGraphDataError(
            f"fichier d'embeddings FlavorGraph introuvable : {path} "
            "(voir backend/data/flavorgraph/README.md)"
        )
    with path.open("rb") as f:
        return pickle.load(f)


@lru_cache(maxsize=1)
def _load_ingredient_name_to_id() -> dict[str, str]:
    path = settings.flavorgraph_dir / NODES_FILENAME
    if not path.exists():
        raise FlavorGraphDataError(
            f"fichier de vocabulaire FlavorGraph introuvable : {path} "
            "(voir backend/data/flavorgraph/README.md)"
        )
    name_to_id: dict[str, str] = {}
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["node_type"] == INGREDIENT_NODE_TYPE:
                name_to_id[row["name"]] = row["node_id"]
    return name_to_id


def get_vector(
    ingredient: str, mapping: dict[str, str] = SOURCE_TO_FLAVORGRAPH
) -> np.ndarray | None:
    """Looks up `ingredient`'s FlavorGraph embedding, translating from the
    app's source-language vocabulary first. Returns None (never raises) for
    anything unmapped or unresolvable — including the data files themselves
    being absent (they're a manually-downloaded, gitignored asset, not
    present in CI or a fresh clone) — callers filter these out rather than
    fail a whole similarity computation over one obscure ingredient or a
    missing optional dataset, but the miss is logged so gaps stay visible."""
    en_name = mapping.get(ingredient.lower())
    if en_name is None:
        logger.info("aucune correspondance FlavorGraph pour l'ingrédient : %r", ingredient)
        return None

    try:
        node_id = _load_ingredient_name_to_id().get(en_name)
    except FlavorGraphDataError as exc:
        logger.warning("données FlavorGraph indisponibles (%s) — vue ingrédients dégradée", exc)
        return None
    if node_id is None:
        logger.warning(
            "ingrédient %r mappé vers %r mais absent du vocabulaire FlavorGraph",
            ingredient,
            en_name,
        )
        return None

    try:
        vector = _load_embeddings().get(node_id)
    except FlavorGraphDataError as exc:
        logger.warning("données FlavorGraph indisponibles (%s) — vue ingrédients dégradée", exc)
        return None
    if vector is None:
        logger.warning(
            "node_id %r (ingrédient %r) présent dans nodes.csv mais absent des embeddings",
            node_id,
            ingredient,
        )
        return None
    return vector
