"""Recipe like table definition — one row per (user, recipe) "like".

Simpler than watchlist_entry: a like carries no notes or planned date, it's a
plain one-per-user-per-recipe marker. The UniqueConstraint enforces "one like
per user per recipe" at the database level; the service layer treats add/remove
as idempotent toggles on top of it.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from veggie_app.database import Base


class RecipeLike(Base):
    __tablename__ = "recipe_likes"
    __table_args__ = (UniqueConstraint("user_id", "recipe_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
