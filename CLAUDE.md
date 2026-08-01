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
Admin (the project owner) adds vegetarian recipes via a CLI script, or via
the admin web interface after logging in (session-cookie auth; see the
"Admin auth" architecture entry in `docs/ARCHITECTURE.md`), one at a time
or in bulk via CSV import. The admin can also list every recipe, and view,
edit, or delete any of them from the web interface.
 
Do not implement features from later phases unless explicitly requested.
See `docs/ROADMAP.md` for the full phase breakdown.
 
## Stack
 
| Layer | Choice | Notes |
|---|---|---|
| Backend | FastAPI (Python) | async, typed, auto Swagger docs |
| ORM / migrations | SQLAlchemy + Alembic | never edit schema manually, always migrate |
| Database | PostgreSQL + `pgvector` extension | embeddings stored natively, no ad-hoc numpy storage |
| Vector column type | `pgvector` (Python package) | SQLAlchemy binding for the `pgvector` Postgres extension |
| Embeddings | `sentence-transformers` (multilingual model) | local, no paid external API |
| Numeric arrays | `numpy` | direct dependency (not just transitive via torch) because `matching/` imports it directly for vector/matrix ops — see the torch/uv lesson in `docs/ARCHITECTURE.md` on why transitive-only deps are fragile |
| Ingredient-set matching | `scipy` (`optimize.linear_sum_assignment`) | Hungarian algorithm for optimal one-to-one ingredient matching between two recipes (Phase 2 ingredients-view similarity) |
| Ingredient embeddings | FlavorGraph pretrained vectors (Apache 2.0) | local data asset (not a pip package), not committed to git — see `backend/data/flavorgraph/README.md` |
| Password hashing | `bcrypt` | industry-standard adaptive hashing for admin credentials |
| Multipart form parsing | `python-multipart` | required by FastAPI's `Form`/`UploadFile` — the admin recipe endpoint needs multipart to accept an optional image alongside text fields |
| Recipe image storage | local disk (`backend/uploads/`, bind-mounted, served via FastAPI `StaticFiles`) | no external/paid storage service; works for the planned VPS/self-hosted deployment target |
| Frontend | React + TypeScript + Vite | strict TS mode |
| Routing | `react-router` | needed once the app has more than one page (admin login/upload) |
| Styling | Tailwind CSS | no scattered custom CSS |
| Class composition | `clsx` + `tailwind-merge` | conditional Tailwind class composition via a `cn()` helper (`src/utils/cn.ts`); tailwind-merge dedupes conflicting utilities |
| Component variants | `class-variance-authority` | typed variant definitions for Button/Badge/Alert, keeps variant logic out of JSX |
| Icons | `lucide-react` | tree-shakeable icon set (ISC licence), no icon font |
| Fonts | `@fontsource-variable/fraunces`, `@fontsource/instrument-sans`, `@fontsource-variable/jetbrains-mono` | self-hosted display/UI/data fonts (docs/FRONTEND.md §3.2), no runtime third-party request |
| Accessible primitives | `@radix-ui/react-label`, `@radix-ui/react-dialog` | unstyled accessible label + dialog (admin delete confirmation) behind the styled UI components |
| Animation | `framer-motion` (v12) | Phase 3 hover/click recipe-grid interaction — `layout` animations handle the coordinated resize of the hovered card *and* its 3 siblings (corner-anchored grow/shrink) via automatic FLIP, without hand-computing a transform per card as plain CSS/anime.js would require |
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
│       │   ├── user.py                # admin login now; general accounts in phase 4
│       │   └── admin_session.py        # opaque session tokens (hashed at rest)
│       ├── schemas/                    # Pydantic request/response models only
│       │   ├── recipe.py
│       │   └── auth.py
│       ├── matching/                   # pure similarity logic, no FastAPI/DB deps
│       │   ├── embeddings.py
│       │   └── similarity.py
│       ├── services/                   # business logic / orchestration
│       │   ├── recipe_service.py
│       │   └── auth_service.py
│       ├── api/routes/                 # thin routes only
│       │   ├── suggestions.py          # POST /suggestions
│       │   ├── auth.py                 # /auth/login, /auth/logout, /auth/me
│       │   └── admin_recipes.py        # /admin/recipes CRUD + /import (admin-only)
│       └── admin/
│           ├── add_recipe_cli.py
│           └── create_admin_cli.py
│   ├── tests/
│   └── scripts/seed_db.py
├── frontend/
│   ├── src/
│   │   ├── api/                       # HTTP calls to backend
│   │   ├── components/                # app components (Header, RecipeForm, ...)
│   │   │   └── ui/                    # styled primitives (Button, Card, Input, ...)
│   │   ├── pages/
│   │   ├── types/
│   │   └── utils/                     # framework-agnostic helpers (cn, motion tokens, ...)
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
uv run python -m veggie_app.admin.create_admin_cli
 
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
8. For any frontend/visual work, read `docs/FRONTEND.md` first and follow it
   exactly (design tokens, dark-green theme, motion system).
 
