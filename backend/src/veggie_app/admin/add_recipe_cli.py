"""Interactive CLI for the admin to add a vegetarian recipe.

Run with: uv run python -m veggie_app.admin.add_recipe_cli
"""

import logging

from veggie_app.database import SessionLocal
from veggie_app.services import recipe_service

# A dedicated, non-propagating handler (rather than logging.basicConfig, which
# configures the root logger) so this stays scoped to our own messages: the
# root logger is shared with sentence-transformers/huggingface_hub, which log
# every HTTP request at INFO and would otherwise drown out the CLI prompts.
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = False
_handler = logging.StreamHandler()
_handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(_handler)


def _prompt_title() -> str:
    while True:
        title = input("Titre de la recette : ").strip()
        if title:
            return title
        logger.warning("Le titre ne peut pas être vide.")


def _prompt_list(prompt: str) -> list[str]:
    raw = input(prompt).strip()
    return [item.strip() for item in raw.split(",") if item.strip()]


def _prompt_ingredients() -> list[str]:
    while True:
        ingredients = _prompt_list("Ingrédients (séparés par des virgules) : ")
        if ingredients:
            return ingredients
        logger.warning("Il faut au moins un ingrédient.")


def _prompt_prep_time() -> int | None:
    raw = input("Temps de préparation en minutes (optionnel) : ").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        logger.warning("Valeur ignorée (nombre entier attendu).")
        return None


def main() -> None:
    title = _prompt_title()
    ingredients = _prompt_ingredients()
    allergens = _prompt_list("Allergènes (optionnel, séparés par des virgules) : ")
    prep_time_minutes = _prompt_prep_time()

    db = SessionLocal()
    try:
        recipe = recipe_service.create_recipe(
            db,
            title=title,
            ingredients=ingredients,
            allergens=allergens,
            prep_time_minutes=prep_time_minutes,
        )
        db.commit()
        recipe_id = recipe.id
    finally:
        db.close()

    logger.info("Recette ajoutée : #%s %s", recipe_id, title)


if __name__ == "__main__":
    main()
