"""convert ingredients to structured name/quantity json

Revision ID: be16d5b1145d
Revises: 66b2be4a7cb8
Create Date: 2026-07-24 16:25:51.318003

`ingredients` moves from a plain text[] (ingredient names only) to a json
column of {"name": ..., "quantity": ...} objects, so a quantity can be
attached per ingredient (required once "servings" is set — see
services/recipe_service.py). Existing rows are converted in place with
quantity left null, not dropped or re-typed by hand.
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'be16d5b1145d'
down_revision: str | Sequence[str] | None = '66b2be4a7cb8'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('recipes', sa.Column('ingredients_new', sa.JSON(), nullable=True))
    op.execute(
        """
        UPDATE recipes
        SET ingredients_new = (
            SELECT COALESCE(
                json_agg(json_build_object('name', elem, 'quantity', NULL)),
                '[]'::json
            )
            FROM unnest(ingredients) AS elem
        )
        """
    )
    op.alter_column('recipes', 'ingredients_new', nullable=False)
    op.drop_column('recipes', 'ingredients')
    op.alter_column('recipes', 'ingredients_new', new_column_name='ingredients')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('recipes', sa.Column('ingredients_old', sa.ARRAY(sa.String()), nullable=True))
    op.execute(
        """
        UPDATE recipes
        SET ingredients_old = (
            SELECT array_agg(elem ->> 'name')
            FROM json_array_elements(ingredients) AS elem
        )
        """
    )
    op.alter_column('recipes', 'ingredients_old', nullable=False)
    op.drop_column('recipes', 'ingredients')
    op.alter_column('recipes', 'ingredients_old', new_column_name='ingredients')
