"""Shared pytest fixtures.

Tests run against the real Postgres instance (see DATABASE_URL) rather than
a mock, since the whole point of pgvector-backed columns is that they only
behave correctly against real Postgres.
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.orm import Session

from veggie_app.database import engine, get_db
from veggie_app.main import app
from veggie_app.models.password_reset_token import PasswordResetToken
from veggie_app.models.recipe import Recipe
from veggie_app.models.user import User
from veggie_app.models.user_preference import UserPreference
from veggie_app.models.user_session import UserSession
from veggie_app.models.watchlist_entry import WatchlistEntry


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    """A DB session wrapped in a transaction that is rolled back after the
    test, so tests never leave rows behind in the dev database.

    Also clears these tables at the start, within this same rolled-back
    transaction: the dev DB accumulates real recipes/admins through normal
    use of the app (CLI, admin UI), and tests need a known-empty starting
    point. Real data is untouched since nothing here is ever committed —
    see the rollback below.
    """
    connection = engine.connect()
    transaction = connection.begin()
    # create_savepoint: app code (auth_service) uses db.begin_nested() around
    # inserts/updates that might violate a unique constraint, so its SAVEPOINT
    # rolls back just that statement instead of unwinding this fixture's
    # outer transaction — the default "conditional_savepoint" mode still
    # deassociates the outer transaction in that case.
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    session.execute(delete(UserSession))
    session.execute(delete(PasswordResetToken))
    session.execute(delete(UserPreference))
    session.execute(delete(WatchlistEntry))
    session.execute(delete(User))
    session.execute(delete(Recipe))
    session.flush()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """A FastAPI TestClient whose get_db dependency is overridden to reuse
    the same rolled-back db_session, so route tests don't touch real data."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
