# CLAUDE.md
 
This file guides Claude Code when working in this repository. Read it fully
before making changes. Do not deviate from the decisions below without
explicit user confirmation.
 
## Project overview
 
Web app that takes a non-vegetarian recipe as input and returns similar
vegetarian recipes (similar in taste and/or composition). Codebase, comments,
and identifiers are in English. **User-facing strings (UI text) are in
French** — this may change later, but do not hardcode English UI text.
 
Long-term scope (not to be built now, listed for context only): vegan
alternatives, dietary restriction filters, nutritional equivalence scoring,
optional user accounts, ratings, tutorial videos, a carbon-footprint
awareness page.
 
## Current phase
 
**Phase 1 — POC.**
Scope: user submits a recipe title (+ ingredients) → API returns 4 similar
vegetarian recipes using embedding similarity (no nutritional scoring yet).
Admin (the project owner) adds vegetarian recipes via a CLI script.
 
Do not implement features from later phases unless explicitly requested.
See `docs/ROADMAP.md` for the full phase breakdown.
 
## Stack
 
| Layer | Choice | Notes |
|---|---|---|
| Backend | FastAPI (Python) | async, typed, auto Swagger docs |
| ORM / migrations | SQLAlchemy + Alembic | never edit schema manually, always migrate |
| Database | PostgreSQL + `pgvector` extension | embeddings stored natively, no ad-hoc numpy storage |
| Embeddings | `sentence-transformers` (multilingual model) | local, no paid external API |
| Frontend | React + TypeScript + Vite | strict TS mode |
| Styling | Tailwind CSS | no scattered custom CSS |
| Containerization | Docker + docker-compose | reproducible env from day one |
| Python deps | `uv` + `pyproject.toml` | |
| Lint/format | `ruff` (backend), ESLint + Prettier (frontend) | |
| Tests | `pytest` (backend), `vitest` (frontend) | |
| CI | GitHub Actions | lint + tests on every push |
 
**Rule:** never introduce a new dependency or tool without adding it to this
table with a one-line justification.
 
## Repository structure
 
```
veggie-app/
├── CLAUDE.md
├── README.md
├── docker-compose.yml
├── .env.example
├── docs/
│   ├── ARCHITECTURE.md
│   └── ROADMAP.md
├── backend/
│   ├── pyproject.toml
│   ├── alembic/versions/
│   └── src/veggie_app/
│       ├── main.py                    # FastAPI entrypoint
│       ├── config.py                  # pydantic-settings, env vars
│       ├── database.py                # engine, session, get_db dependency
│       ├── models/                    # SQLAlchemy tables only
│       │   ├── recipe.py
│       │   └── user.py                # scaffolded, unused in phase 1
│       ├── schemas/                    # Pydantic request/response models only
│       │   └── recipe.py
│       ├── matching/                   # pure similarity logic, no FastAPI/DB deps
│       │   ├── embeddings.py
│       │   └── similarity.py
│       ├── services/                   # business logic / orchestration
│       │   └── recipe_service.py
│       ├── api/routes/                 # thin routes only
│       │   ├── suggestions.py          # POST /suggestions
│       │   └── admin_recipes.py
│       └── admin/
│           └── add_recipe_cli.py
│   ├── tests/
│   └── scripts/seed_db.py
├── frontend/
│   ├── src/
│   │   ├── api/                       # HTTP calls to backend
│   │   ├── components/
│   │   ├── pages/
│   │   └── types/
│   └── tests/
└── .github/workflows/ci.yml
```
 
## Architectural rules
 
- `api/routes/*`: input validation (via `schemas/`) + call a service +
  serialize output. **No business logic.**
- `services/*`: orchestrates business logic, calls `matching/` and `models/`.
- `matching/*`: pure functions (data in, data out). No FastAPI or DB session
  dependency. This isolation is what allows swapping the similarity function
  for a multi-criteria score (nutrition, calories) in a later phase without
  touching routes or frontend.
- `models/*`: table definitions only, no logic.
- `schemas/*`: Pydantic validation/serialization only, no logic.
- Never bypass Alembic for schema changes.
## Code conventions
 
- Python: `snake_case`, type hints on every function, no bare `print()` — use
  `logging`.
- TypeScript/React: `camelCase` for variables/functions, `PascalCase` for
  components and classes, `strict: true` in `tsconfig.json`.
- Every new function in `matching/` or `services/` needs a test.
- Every new dependency must be added to the stack table above with a reason.
- Commit convention: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`.
  One commit = one logical change.
## Commands
 
```bash
# Full environment (Postgres + backend)
docker-compose up --build
 
# Backend
cd backend
uv sync
uv run pytest
uv run ruff check .
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
uv run python -m veggie_app.admin.add_recipe_cli
 
# Frontend
cd frontend
npm install
npm run dev
npm run test
npm run lint
```
 
## Checklist before implementing a feature
 
1. Confirm the current phase in `docs/ROADMAP.md` — do not build ahead of it
   unless explicitly asked.
2. Follow the repository structure above; do not add top-level folders
   without updating this file.
3. Keep business logic out of API routes.
4. Add a test for any new `matching/` or `services/` function.
5. Document non-trivial architecture decisions in `docs/ARCHITECTURE.md`.
6. Do not introduce tools outside the stack table without explicit user
   approval.
7. Keep UI-facing strings in French; keep code (identifiers, comments,
   commit messages) in English.
 
