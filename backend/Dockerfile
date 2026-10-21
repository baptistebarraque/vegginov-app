FROM python:3.11-slim

# Pinned (not :latest) so a new uv release can't silently change how the
# image builds; same version as the dev machine. Bump deliberately.
COPY --from=ghcr.io/astral-sh/uv:0.11.28 /uv /uvx /bin/

WORKDIR /app

# Install dependencies first, separately from app code, so this layer is
# cached and only re-runs when pyproject.toml/uv.lock actually change.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY src ./src
COPY alembic.ini ./
COPY alembic ./alembic
RUN uv sync --frozen

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "veggie_app.main:app", "--host", "0.0.0.0", "--port", "8000"]
