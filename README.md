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

**Phase 4 — POC.** Optional users account, favorite recipes, "to do list".

---

## Tech stack

- **Backend**: FastAPI, SQLAlchemy, Alembic
- **Database**: PostgreSQL (`pgvector` extension for embeddings)
- **Similarity**: `sentence-transformers` (multilingual model)
- **Admin auth**: `bcrypt` password hashing, server-side sessions (httpOnly cookie)
- **Frontend**: React + TypeScript + Vite, `react-router`, Tailwind CSS
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



### 4. Start the frontend (outside Docker for now)

```bash
cd frontend
npm install
npm run dev
```

The frontend is available at `http://localhost:5173`.

---

## Adding a vegetarian recipe (admin)

Recipes can be added two ways:

- **CLI script**, prompts for a title, ingredients, and optional tags
  (allergens, prep time...); the embedding is generated and stored
  automatically:

  ```bash
  docker-compose exec backend uv run python -m veggie_app.admin.add_recipe_cli
  ```

- **Admin web interface**, at `/admin/login` on the frontend. Requires an
  admin account, created once via CLI (`getpass`-prompted, so the password
  never touches this terminal's scrollback):

  ```bash
  docker-compose exec backend uv run python -m veggie_app.admin.create_admin_cli
  ```

  The same admin page also has a **CSV import** section for adding many
  recipes at once — columns match the single-recipe fields (`title`,
  `ingredients` required; `allergens`, `prep_time_minutes`, `servings`,
  `protein_source`, `protein_grams`, `instructions` optional), with
  multi-value cells separated by `;`. Each ingredient can carry a quantity
  after a colon, e.g. `riz:200g; curry` — **required** for every ingredient
  once `servings` is filled in. A downloadable template is linked from
  that page. The whole file is validated before anything is imported —
  one bad row reports every error and imports nothing.

  From `/admin/recipes`, the admin can see every recipe (title +
  thumbnail), and open one to edit any field or delete it entirely.

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

## Deployment (production)

Production adds Caddy in front of the app (`docker-compose.prod.yml`): it
serves the built frontend, forwards `/api/*` to the backend, and gets free
HTTPS certificates from Let's Encrypt on its own. Only ports 80 and 443 are
open to the network; Postgres and the backend stay on `127.0.0.1`.

1. On the server, copy `.env.example` to `.env` and set:
   - `SITE_ADDRESS` — your domain (e.g. `vegginov.fr`), whose DNS points at
     the server
   - `POSTGRES_PASSWORD` — a generated one:
     `python -c "import secrets; print(secrets.token_urlsafe(32))"`
     (docker-compose builds the backend's database URL from it;
     `DATABASE_URL` in `.env` only serves runs outside Docker)
   The overlay itself sets `APP_ENV=production`, and the backend refuses to
   start on the dev password or on non-https origins.
2. Start it and apply migrations:
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
   docker compose exec backend alembic upgrade head
   ```
3. Create the admin account:
   `docker compose exec backend python -m veggie_app.admin.create_admin_cli`

To try it on a dev PC first, leave `SITE_ADDRESS` unset: it serves
`https://localhost` with a local certificate (the browser warns once). The
backend then also needs a non-default DB password, so use a separate
project name and volume rather than the dev database.

Password-reset links are written to the backend log until email delivery
exists: `docker compose logs backend | grep "reset link"`.

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
