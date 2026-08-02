"""add calories and price tier to recipes

Revision ID: d4e7a1b9c2f3
Revises: a7f386aeee9f
Create Date: 2026-08-02 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd4e7a1b9c2f3'
down_revision: str | Sequence[str] | None = 'a7f386aeee9f'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('recipes', sa.Column('calories_per_portion', sa.Float(), nullable=True))
    op.add_column('recipes', sa.Column('price_tier', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('recipes', 'price_tier')
    op.drop_column('recipes', 'calories_per_portion')
