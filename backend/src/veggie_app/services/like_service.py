"""Business logic for recipe likes ("one like per user per recipe").

Structurally a lighter twin of watchlist_service: add/remove are idempotent
toggles, list_for_user powers the "liked recipes" view, and liked_recipe_ids
lets a suggestions response flag each recipe as liked-by-me without an N+1
query. The extra piece here — like_counts — exists because a like *count* is
public (shown on every recipe), whereas a watchlist is private.
"""

from collections.abc import Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from veggie_app.models.recipe import Recipe
from veggie_app.models.recipe_like import RecipeLike


def get_like(db: Session, user_id: int, recipe_id: int) -> RecipeLike | None:
    return db.execute(
        select(RecipeLike).where(
            RecipeLike.user_id == user_id, RecipeLike.recipe_id == recipe_id
        )
    ).scalar_one_or_none()


def add(db: Session, user_id: int, recipe_id: int) -> RecipeLike:
    """Idempotent: liking an already-liked recipe returns the existing like
    instead of raising or creating a duplicate — matches the frontend's
    like/unlike toggle rather than a strict create-once API. Same reasoning as
    watchlist_service.add.
    """
    existing = get_like(db, user_id, recipe_id)
    if existing is not None:
        return existing
    like = RecipeLike(user_id=user_id, recipe_id=recipe_id)
    db.add(like)
    db.flush()
    return like


def remove(db: Session, user_id: int, recipe_id: int) -> None:
    """Idempotent: unliking a recipe that isn't liked is a no-op."""
    like = get_like(db, user_id, recipe_id)
    if like is not None:
        db.delete(like)
        db.flush()


def list_for_user(db: Session, user_id: int) -> list[tuple[RecipeLike, Recipe]]:
    rows = db.execute(
        select(RecipeLike, Recipe)
        .join(Recipe, Recipe.id == RecipeLike.recipe_id)
        .where(RecipeLike.user_id == user_id)
        # id, not created_at: within one transaction Postgres's now() is frozen
        # at transaction start, so likes added back-to-back in the same
        # transaction (as tests do) would tie on created_at — id is monotonic
        # per insert regardless of transaction timing. Same reasoning as
        # watchlist_service.list_for_user.
        .order_by(RecipeLike.id.desc())
    ).all()
    return [(like, recipe) for like, recipe in rows]


def liked_recipe_ids(db: Session, user_id: int) -> set[int]:
    """Used by recipe_service.get_suggestions to compute is_liked per
    suggestion without an N+1 query."""
    rows = (
        db.execute(select(RecipeLike.recipe_id).where(RecipeLike.user_id == user_id))
        .scalars()
        .all()
    )
    return set(rows)


def like_counts(db: Session, recipe_ids: Iterable[int]) -> dict[int, int]:
    """Number of likes per recipe, for the given recipe ids, as a dict.

    Batched (one grouped query) so get_suggestions can attach a public
    like_count to each of its results without a per-recipe query. Recipes with
    no likes are simply absent from the dict — callers use dict.get(id, 0).
    """
    ids = list(recipe_ids)
    if not ids:
        return {}
    rows = db.execute(
        select(RecipeLike.recipe_id, func.count())
        .where(RecipeLike.recipe_id.in_(ids))
        .group_by(RecipeLike.recipe_id)
    ).all()
    return {recipe_id: count for recipe_id, count in rows}
