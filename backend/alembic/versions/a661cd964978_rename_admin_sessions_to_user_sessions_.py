"""rename admin_sessions to user_sessions, add password_reset_tokens

Revision ID: a661cd964978
Revises: d4e7a1b9c2f3
Create Date: 2026-08-03 20:43:00.327018

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a661cd964978'
down_revision: str | Sequence[str] | None = 'd4e7a1b9c2f3'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename in place (not drop+create) to keep any existing admin sessions
    # valid, rather than forcing every logged-in admin to re-login.
    op.rename_table('admin_sessions', 'user_sessions')
    op.drop_constraint('admin_sessions_user_id_fkey', 'user_sessions', type_='foreignkey')
    op.create_foreign_key(
        'user_sessions_user_id_fkey', 'user_sessions', 'users', ['user_id'], ['id'],
        ondelete='CASCADE',
    )

    op.create_table('password_reset_tokens',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('token_hash')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('password_reset_tokens')

    op.drop_constraint('user_sessions_user_id_fkey', 'user_sessions', type_='foreignkey')
    op.create_foreign_key(
        'admin_sessions_user_id_fkey', 'user_sessions', 'users', ['user_id'], ['id'],
    )
    op.rename_table('user_sessions', 'admin_sessions')
