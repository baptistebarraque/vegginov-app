"""Business logic for a user's recipe watchlist ("save for later")."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from veggie_app.models.recipe import Recipe
from veggie_app.models.watchlist_entry import WatchlistEntry


def get_entry(db: Session, user_id: int, recipe_id: int) -> WatchlistEntry | None:
    return db.execute(
        select(WatchlistEntry).where(
            WatchlistEntry.user_id == user_id, WatchlistEntry.recipe_id == recipe_id
        )
    ).scalar_one_or_none()


def add(db: Session, user_id: int, recipe_id: int) -> WatchlistEntry:
    """Idempotent: saving an already-saved recipe returns the existing entry
    instead of raising or creating a duplicate — matches the frontend's
    add/remove toggle button rather than a strict create-once API.
    """
    existing = get_entry(db, user_id, recipe_id)
    if existing is not None:
        return existing
    entry = WatchlistEntry(user_id=user_id, recipe_id=recipe_id)
    db.add(entry)
    db.flush()
    return entry


def remove(db: Session, user_id: int, recipe_id: int) -> None:
    """Idempotent: removing an entry that isn't there is a no-op, same
    reasoning as add()."""
    entry = get_entry(db, user_id, recipe_id)
    if entry is not None:
        db.delete(entry)
        db.flush()


def update_entry(
    db: Session,
    user_id: int,
    recipe_id: int,
    *,
    notes: str | None,
    planned_for: date | None,
) -> WatchlistEntry | None:
    entry = get_entry(db, user_id, recipe_id)
    if entry is None:
        return None
    entry.notes = notes
    entry.planned_for = planned_for
    db.flush()
    return entry


def list_for_user(db: Session, user_id: int) -> list[tuple[WatchlistEntry, Recipe]]:
    rows = db.execute(
        select(WatchlistEntry, Recipe)
        .join(Recipe, Recipe.id == WatchlistEntry.recipe_id)
        .where(WatchlistEntry.user_id == user_id)
        # id, not created_at: within one transaction Postgres's now() is
        # frozen at transaction start, so entries added back-to-back in the
        # same transaction (as tests do) would tie on created_at — id is
        # monotonic per insert regardless of transaction timing.
        .order_by(WatchlistEntry.id.desc())
    ).all()
    return [(entry, recipe) for entry, recipe in rows]


def watchlisted_recipe_ids(db: Session, user_id: int) -> set[int]:
    """Used by recipe_service.get_suggestions to compute is_watchlisted per
    suggestion without an N+1 query."""
    rows = (
        db.execute(select(WatchlistEntry.recipe_id).where(WatchlistEntry.user_id == user_id))
        .scalars()
        .all()
    )
    return set(rows)
