"""One-off maintenance script: recomputes every recipe's stored embedding
from its title alone.

Needed once, the day `Recipe.embedding` changed meaning from "title +
ingredient names" to "title only" (see docs/ARCHITECTURE.md's "Ingredients
view + Title view fusion" entry) — existing rows created before that change
still hold the old (title + ingredients) embedding, which isn't comparable
to new title-only embeddings. Safe to re-run (idempotent).

Run with: uv run python -m scripts.recompute_title_embeddings
"""

import logging

from veggie_app.database import SessionLocal
from veggie_app.matching.embeddings import embed_text
from veggie_app.models.recipe import Recipe

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = False
_handler = logging.StreamHandler()
_handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(_handler)


def main() -> None:
    db = SessionLocal()
    try:
        recipes = db.query(Recipe).all()
        for recipe in recipes:
            recipe.embedding = embed_text(recipe.title)
        db.commit()
        logger.info("%d recette(s) recalculée(s).", len(recipes))
    finally:
        db.close()


if __name__ == "__main__":
    main()
