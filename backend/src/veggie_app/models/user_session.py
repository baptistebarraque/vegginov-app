"""Session table definition.

Named UserSession (table user_sessions), not Session, to avoid colliding
with sqlalchemy.orm.Session which every service function takes as a param.
Used for both admin and regular-user logins (see auth_service.require_user /
require_admin) — not admin-specific despite the original admin-only name.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from veggie_app.database import Base


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # sha256 hex digest of the session token, not the raw token, so a DB leak
    # alone doesn't hand out valid sessions (same reasoning as password_hash).
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
