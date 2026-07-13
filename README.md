# Veggie App

A web app that takes the title (and/or ingredients) of a non-vegetarian recipe
and returns similar vegetarian recipe suggestions, matched by taste and/or
composition.

Long-term goals: dietary restriction filters (allergies, gluten...),
nutritional equivalence (calories, protein), optional user accounts, a rating
system, tutorial videos, and a carbon-footprint awareness page.

Note: the codebase (identifiers, comments, commit messages) is in English.
User-facing UI text is currently in French.

📄 For detailed technical architecture and coding conventions, see
[`CLAUDE.md`](./CLAUDE.md). For the detailed roadmap, see
[`docs/ROADMAP.md`](./docs/ROADMAP.md).

---

## Current status

**Phase 1 — POC.** User submits a recipe, the app returns 4 similar
vegetarian recipes (the similarity is yet to define). An admin can add vegetarian
recipes via a CLI script.

---

## Tech stack

- **Backend**: FastAPI, SQLAlchemy, Alembic
- **Database**: PostgreSQL (`pgvector` extension for embeddings)
- **Similarity**: `sentence-transformers` (multilingual model)
- **Frontend**: React + TypeScript + Vite, Tailwind CSS
- **Environment**: Docker / docker-compose
- **Quality**: ruff (lint), pytest / vitest (tests), GitHub Actions (CI)

See `CLAUDE.md` section "Stack" for the full rationale behind each choice.

---

## Prerequisites

- Docker and docker-compose installed
- Python 3.11+ and [`uv`](https://github.com/astral-sh/uv) (for working on the
  backend outside Docker)
- Node.js 20+ (for working on the frontend outside Docker)

---

## Setup and run

### 1. Clone the project and configure the environment

```bash
git clone <repo-url>
cd veggie-app
cp .env.example .env
# Edit .env if needed (Postgres credentials, etc.)
```

### 2. Start everything (Postgres + backend) via Docker

```bash
docker-compose up --build
```

The backend is then available at `http://localhost:8000`, with Swagger docs
at `http://localhost:8000/docs`.

### 3. Apply database migrations

```bash
docker-compose exec backend uv run alembic upgrade head
```

### 4. Seed the database with sample vegetarian recipes

```bash
docker-compose exec backend uv run python -m veggie_app.scripts.seed_db
```

### 5. Start the frontend (outside Docker for now)

```bash
cd frontend
npm install
npm run dev
```

The frontend is available at `http://localhost:5173`.

---

## Adding a vegetarian recipe (admin)

In phase 1, recipes are added through a CLI script:

```bash
docker-compose exec backend uv run python -m veggie_app.admin.add_recipe_cli
```

The script prompts for a title, ingredients, and optional tags (allergens,
prep time...). The embedding is generated and stored automatically.

---

## Tests and code quality

```bash
# Backend
cd backend
uv run ruff check .
uv run pytest

# Frontend
cd frontend
npm run lint
npm run test
```

CI (GitHub Actions) runs these checks automatically on every push.

---

## Project structure

See the "Repository structure" section of [`CLAUDE.md`](./CLAUDE.md) for the
full folder layout and the separation-of-concerns rules between routes,
services, and matching logic.

---

## Roadmap (summary)

| Phase | Goal |
|---|---|
| 0 | Setup (repo, CI, Docker, structure) |
| 1 | POC: suggest 4 vegetarian recipes by similarity, admin CLI |
| 2 | Simple filters (allergies, gluten), basic rating |
| 3 | Combined score (similarity + nutritional equivalence), real ranking |
| 4 | Optional user accounts, favorite recipes |
| 5 | Tutorial videos, carbon-footprint awareness page, comments |
| 6 | Vegan extension, larger-scale recipe sourcing |

Full detail in [`docs/ROADMAP.md`](./docs/ROADMAP.md).

---

## Contributing (conventions)

- Commit convention: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`.
- Every new feature must come with at least one test.
- Every new dependency must be documented and justified in `CLAUDE.md`.
- Any database schema change goes through a versioned Alembic migration.