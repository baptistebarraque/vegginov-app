"""Business logic for the admin's read-only view of every account.

Separate from auth_service, which owns credentials/sessions for the *current*
user: this module never authenticates anyone, it only aggregates what an admin
is shown about other accounts. Password hashes are deliberately never part of
what it returns.
"""

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import InstrumentedAttribute, Session

from veggie_app.models.recipe import Recipe
from veggie_app.models.recipe_like import RecipeLike
from veggie_app.models.user import User
from veggie_app.models.user_preference import UserPreference
from veggie_app.models.watchlist_entry import WatchlistEntry
from veggie_app.services import like_service, preference_service, watchlist_service


@dataclass(frozen=True)
class UserSummary:
    """One account plus the per-account totals the admin list column shows."""

    user: User
    watchlist_count: int
    like_count: int
    has_preferences: bool


@dataclass(frozen=True)
class UserDetail:
    """Everything the admin detail view shows about one account."""

    summary: UserSummary
    preferences: UserPreference | None
    watchlist: list[tuple[WatchlistEntry, Recipe]]
    likes: list[tuple[RecipeLike, Recipe]]


def _counts_by_user(db: Session, column: InstrumentedAttribute[int]) -> dict[int, int]:
    """Rows grouped by user_id, as {user_id: count}.

    One grouped query per relation instead of a COUNT per user, so listing N
    accounts stays 4 queries rather than 1 + 3N.
    """
    rows = db.execute(select(column, func.count()).group_by(column)).all()
    return {user_id: count for user_id, count in rows}


def list_user_summaries(db: Session) -> list[UserSummary]:
    watchlist_counts = _counts_by_user(db, WatchlistEntry.user_id)
    like_counts = _counts_by_user(db, RecipeLike.user_id)
    preference_user_ids = set(db.execute(select(UserPreference.user_id)).scalars().all())
    # id, not created_at: within one transaction Postgres's now() is frozen at
    # transaction start, so accounts created back-to-back in the same
    # transaction (as tests do) would tie on created_at — id is monotonic per
    # insert regardless of transaction timing. Same reasoning as
    # watchlist_service.list_for_user. Newest account first.
    users = db.execute(select(User).order_by(User.id.desc())).scalars().all()
    return [
        UserSummary(
            user=user,
            watchlist_count=watchlist_counts.get(user.id, 0),
            like_count=like_counts.get(user.id, 0),
            has_preferences=user.id in preference_user_ids,
        )
        for user in users
    ]


def get_user_detail(db: Session, user_id: int) -> UserDetail | None:
    """None when no such account exists — the route turns that into a 404."""
    user = db.get(User, user_id)
    if user is None:
        return None

    preferences = preference_service.get_preferences(db, user_id)
    watchlist = watchlist_service.list_for_user(db, user_id)
    likes = like_service.list_for_user(db, user_id)
    return UserDetail(
        summary=UserSummary(
            user=user,
            watchlist_count=len(watchlist),
            like_count=len(likes),
            has_preferences=preferences is not None,
        ),
        preferences=preferences,
        watchlist=watchlist,
        likes=likes,
    )
