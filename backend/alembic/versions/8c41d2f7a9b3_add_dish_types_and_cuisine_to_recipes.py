"""add dish types and cuisine to recipes

Revision ID: 8c41d2f7a9b3
Revises: e2c7b3a95f14
Create Date: 2026-10-17 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '8c41d2f7a9b3'
down_revision: str | Sequence[str] | None = 'e2c7b3a95f14'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # server_default fills the existing rows: untagged until tagged.
    op.add_column(
        'recipes',
        sa.Column(
            'dish_types',
            sa.ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
    )
    op.add_column('recipes', sa.Column('cuisine', sa.String(length=64), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('recipes', 'cuisine')
    op.drop_column('recipes', 'dish_types')
