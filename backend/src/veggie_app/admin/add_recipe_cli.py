"""Interactive CLI for the admin to add a vegetarian recipe.

Run with: uv run python -m veggie_app.admin.add_recipe_cli
"""

import logging
from pathlib import Path

from veggie_app.database import SessionLocal
from veggie_app.models.recipe import IngredientEntry
from veggie_app.services import image_service, recipe_service
from veggie_app.services.image_service import InvalidImageError
from veggie_app.services.recipe_service import IngredientQuantityError

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


def _prompt_ingredients(servings: int | None) -> list[IngredientEntry]:
    quantity_required = servings is not None
    logger.info(
        "Ingrédients (un par ligne, ligne vide pour terminer%s) :",
        " ; quantité obligatoire puisque le nombre de personnes est renseigné"
        if quantity_required
        else "",
    )
    ingredients: list[IngredientEntry] = []
    while True:
        name = input(f"  Ingrédient {len(ingredients) + 1} (nom, vide pour terminer) : ").strip()
        if not name:
            if ingredients:
                return ingredients
            logger.warning("Il faut au moins un ingrédient.")
            continue
        while True:
            quantity = input(f"    Quantité pour '{name}' : ").strip()
            if quantity or not quantity_required:
                break
            logger.warning(
                "La quantité est obligatoire quand le nombre de personnes est renseigné."
            )
        ingredients.append({"name": name, "quantity": quantity or None})


def _prompt_prep_time() -> int | None:
    raw = input("Temps de préparation en minutes (optionnel) : ").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        logger.warning("Valeur ignorée (nombre entier attendu).")
        return None


def _prompt_servings() -> int | None:
    raw = input("Nombre de personnes (optionnel) : ").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        logger.warning("Valeur ignorée (nombre entier attendu).")
        return None


def _prompt_protein_grams() -> float | None:
    raw = input("Protéines en grammes (optionnel) : ").strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        logger.warning("Valeur ignorée (nombre attendu).")
        return None


def _prompt_instructions() -> list[str]:
    logger.info("Étapes de préparation (optionnel, une étape par ligne, ligne vide pour finir) :")
    steps = []
    while True:
        step = input(f"  Étape {len(steps) + 1} : ").strip()
        if not step:
            return steps
        steps.append(step)


def _prompt_image_filename() -> str | None:
    while True:
        raw = input("Chemin vers une photo PNG/JPEG (optionnel) : ").strip()
        if not raw:
            return None
        path = Path(raw)
        try:
            return image_service.save_recipe_image(path.name, path.read_bytes())
        except FileNotFoundError:
            logger.warning("Fichier introuvable : %s", raw)
        except InvalidImageError as exc:
            logger.warning("%s", exc)


def main() -> None:
    title = _prompt_title()
    servings = _prompt_servings()
    ingredients = _prompt_ingredients(servings)
    allergens = _prompt_list("Allergènes (optionnel, séparés par des virgules) : ")
    prep_time_minutes = _prompt_prep_time()
    protein_source = input("Source de protéines (optionnel) : ").strip() or None
    protein_grams = _prompt_protein_grams()
    instructions = _prompt_instructions()
    image_filename = _prompt_image_filename()

    db = SessionLocal()
    try:
        try:
            recipe = recipe_service.create_recipe(
                db,
                title=title,
                ingredients=ingredients,
                allergens=allergens,
                prep_time_minutes=prep_time_minutes,
                servings=servings,
                protein_source=protein_source,
                protein_grams=protein_grams,
                instructions=instructions,
                image_filename=image_filename,
            )
        except IngredientQuantityError as exc:
            logger.warning("%s", exc)
            return
        db.commit()
        recipe_id = recipe.id
    finally:
        db.close()

    logger.info("Recette ajoutée : #%s %s", recipe_id, title)


if __name__ == "__main__":
    main()
