"""User preference table definition.

One row per user (unique user_id), created lazily on first PUT /preferences
rather than at signup — accounts are optional and preferences are too,
per docs/ROADMAP.md.
"""

from sqlalchemy import ARRAY, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from veggie_app.database import Base


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    calorie_orientation: Mapped[str | None] = mapped_column(String(20), nullable=True)
    diet: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # Free-form, same vocabulary as Recipe.allergens (admin types arbitrary
    # strings there too — no fixed enum to match against).
    allergens: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    # Reuses the recipes.price_tier 1..3 scale (services/recipe_service.py's
    # MAX_PRICE_TIER) instead of inventing a second cost scale.
    price_range: Mapped[int | None] = mapped_column(Integer, nullable=True)
