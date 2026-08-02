"""Recipe table definition."""

from datetime import datetime
from typing import TypedDict

from pgvector.sqlalchemy import Vector
from sqlalchemy import ARRAY, JSON, DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from veggie_app.database import Base
from veggie_app.matching.embeddings import EMBEDDING_DIM


class IngredientEntry(TypedDict):
    name: str
    quantity: str | None


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    ingredients: Mapped[list[IngredientEntry]] = mapped_column(JSON, nullable=False)
    allergens: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    prep_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    servings: Mapped[int | None] = mapped_column(Integer, nullable=True)
    protein_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # All nutrition figures are per portion (independent of `servings`).
    protein_grams: Mapped[float | None] = mapped_column(Float, nullable=True)
    calories_per_portion: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Cost indicator on a 1..3 scale (1 = cheapest), rendered as € symbols in
    # the UI. Stored as an int so it stays sortable and easy to extend.
    price_tier: Mapped[int | None] = mapped_column(Integer, nullable=True)
    instructions: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    image_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
