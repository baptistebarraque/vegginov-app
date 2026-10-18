"""Applies dish-structure tags (Recipe.dish_types / Recipe.cuisine) from a JSON
file keyed by recipe title — by default data/recipe_tags.json.

Run with (from backend/):
    uv run python -m scripts.apply_recipe_tags --dry-run
    uv run python -m scripts.apply_recipe_tags
    uv run python -m scripts.apply_recipe_tags path/to/tags.json

Only the two tag columns are written: unlike an edit through the admin form,
nothing else changes and no embedding is recomputed. Every tag is validated
against the vocabularies first (recipe_service.validate_dish_structure), and
nothing is written if any entry is invalid. Every row with a matching title is
tagged, so duplicate titles get the same tags. Titles of the file absent from
the table, and recipes the file doesn't cover, are listed so drift between the
two stays visible.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from sqlalchemy import select

from veggie_app.database import SessionLocal
from veggie_app.models.recipe import Recipe
from veggie_app.services import recipe_service
from veggie_app.services.recipe_service import DishStructureError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = False
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(_handler)

DEFAULT_TAGS_PATH = Path(__file__).resolve().parent.parent / "data" / "recipe_tags.json"


def load_tags(path: Path) -> dict[str, tuple[list[str], str | None]]:
    """title -> (dish types, cuisine), every entry validated. Raises
    DishStructureError naming the first invalid title."""
    raw = json.loads(path.read_text(encoding="utf-8"))["tags"]
    tags = {}
    for title, entry in raw.items():
        dish_types, cuisine = list(entry.get("dish_types", [])), entry.get("cuisine")
        try:
            recipe_service.validate_dish_structure(dish_types, cuisine)
        except DishStructureError as exc:
            raise DishStructureError(f"{title!r} : {exc}") from exc
        tags[title] = (dish_types, cuisine)
    return tags


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("tags_path", type=Path, nargs="?", default=DEFAULT_TAGS_PATH)
    parser.add_argument("--dry-run", action="store_true", help="report, write nothing")
    args = parser.parse_args()

    try:
        tags = load_tags(args.tags_path)
    except DishStructureError as exc:
        logger.error("étiquette invalide, rien n'a été écrit — %s", exc)
        return 1

    db = SessionLocal()
    try:
        recipes = list(db.execute(select(Recipe)).scalars().all())
        # Read before commit/rollback, which expire the loaded rows.
        titles = {recipe.title for recipe in recipes}
        tagged = 0
        for recipe in recipes:
            if recipe.title in tags:
                recipe.dish_types, recipe.cuisine = tags[recipe.title]
                tagged += 1
        if args.dry_run:
            db.rollback()
        else:
            db.commit()
    finally:
        db.close()

    not_in_db = sorted(set(tags) - titles)
    not_in_file = sorted(titles - set(tags))
    verb = "seraient étiquetées" if args.dry_run else "étiquetées"
    logger.info("%d recette(s) %s sur %d.", tagged, verb, len(recipes))
    if not_in_file:
        logger.info(
            "Recettes sans entrée dans le fichier (%d) : %s",
            len(not_in_file),
            ", ".join(not_in_file),
        )
    if not_in_db:
        logger.info(
            "Titres du fichier absents de la base (%d) : %s", len(not_in_db), ", ".join(not_in_db)
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
