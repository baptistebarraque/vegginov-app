"""Bulk-import a recipe CSV directly against the database, bypassing HTTP.

Run with:
    uv run python -m scripts.import_recipes_csv \
        ../../"CC0 DB"/vegginov_import_13k_main_dishes_fr_enriched.csv
    uv run python -m scripts.import_recipes_csv <path> --dry-run
    uv run python -m scripts.import_recipes_csv <path> --batch-size 500

Same parser and same validation as `POST /admin/recipes/import` — it calls
`recipe_import_service.parse_csv`, so a file this script accepts is a file the
web importer would accept, and vice versa. What differs is everything around it:

* **No request to time out.** The endpoint embeds every title inside one
  synchronous HTTP call; at ~18 ms per title a 4087-row file needs well over a
  minute of model time before the response can start, which a reverse proxy in
  front of the app will usually cut off. Nothing here is behind a socket.
* **Committed in batches, not once at the end.** The endpoint's single commit is
  right for a small correction file — the whole upload lands or none of it does.
  For a bulk load it means a failure at row 4000 throws away the first 3999, so
  this commits every `--batch-size` recipes and reports progress. Validation is
  still all-or-nothing and happens up front, so a *content* error still stops the
  run before anything is written; only an infrastructure failure mid-run can
  leave a partial import, and the summary says exactly how far it got.
* **Refuses to double-import.** Re-running a bulk load silently duplicates
  thousands of recipes, and there is no unique constraint on the title to stop
  it. Titles already present are skipped, so a re-run after a partial failure
  resumes instead of duplicating. `--allow-duplicates` opts out.
"""

import argparse
import logging
import sys
import time
from pathlib import Path

from sqlalchemy import select

from veggie_app.database import SessionLocal
from veggie_app.models.recipe import Recipe
from veggie_app.services import recipe_import_service, recipe_service
from veggie_app.services.recipe_import_service import CsvImportError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = False
_handler = logging.StreamHandler()
_handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(_handler)

DEFAULT_BATCH_SIZE = 250


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path, help="CSV to import")
    parser.add_argument("--dry-run", action="store_true", help="validate and report, write nothing")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"commit every N recipes (default {DEFAULT_BATCH_SIZE})",
    )
    parser.add_argument(
        "--allow-duplicates",
        action="store_true",
        help="import titles that already exist in the database",
    )
    args = parser.parse_args()

    if not args.csv_path.is_file():
        logger.error("Fichier introuvable : %s", args.csv_path)
        return 1

    # utf-8-sig so a BOM-prefixed export (what GET /admin/recipes/export emits)
    # round-trips back in unchanged.
    content = args.csv_path.read_text(encoding="utf-8-sig")

    try:
        rows = recipe_import_service.parse_csv(content)
    except CsvImportError as exc:
        logger.error("CSV invalide : %d ligne(s) en erreur.", len(exc.errors))
        for error in exc.errors[:20]:
            logger.error("  ligne %d : %s", error.row_number, error.message)
        if len(exc.errors) > 20:
            logger.error("  ... et %d autre(s).", len(exc.errors) - 20)
        return 1

    logger.info("%d recette(s) valide(s) dans %s.", len(rows), args.csv_path.name)

    db = SessionLocal()
    try:
        existing = set(db.execute(select(Recipe.title)).scalars().all())
        logger.info("%d recette(s) déjà en base.", len(existing))

        if not args.allow_duplicates:
            before = len(rows)
            rows = [row for row in rows if row["title"] not in existing]
            skipped = before - len(rows)
            if skipped:
                logger.info("%d ignorée(s) : titre déjà présent.", skipped)

        if not rows:
            logger.info("Rien à importer.")
            return 0

        if args.dry_run:
            logger.info("--dry-run : %d recette(s) seraient importées.", len(rows))
            return 0

        logger.info("Import de %d recette(s), commit tous les %d...", len(rows), args.batch_size)
        started = time.perf_counter()
        created = 0
        for row in rows:
            recipe_service.create_recipe(db, **row)
            created += 1
            if created % args.batch_size == 0:
                db.commit()
                elapsed = time.perf_counter() - started
                rate = created / elapsed
                remaining = (len(rows) - created) / rate if rate else 0
                logger.info(
                    "  %d/%d  (%.0f/s, ~%.0f s restantes)", created, len(rows), rate, remaining
                )
        db.commit()

        elapsed = time.perf_counter() - started
        logger.info("Terminé : %d recette(s) importée(s) en %.0f s.", created, elapsed)
        return 0
    except Exception:
        db.rollback()
        # The batches already committed stay committed on purpose — re-running
        # skips them by title rather than duplicating them.
        logger.exception("Échec de l'import ; le lot en cours a été annulé.")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
