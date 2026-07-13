# Roadmap

This is the authoritative phase breakdown. `CLAUDE.md` and `README.md` only
carry a summary — check here to confirm what is in/out of scope before
building anything.

## Phase 0 — Setup

Repository structure, Docker/docker-compose, backend and frontend skeletons,
CI (lint + tests on every push). No product features yet.

## Phase 1 — POC (current phase)

- User submits a recipe title (+ ingredients).
- API returns 4 similar vegetarian recipes, ranked by embedding similarity
  only (no nutritional scoring).
- Admin (project owner) adds vegetarian recipes one at a time via a CLI
  script (`admin/add_recipe_cli.py`); embeddings generated and stored
  automatically.
- No user accounts, no filters, no ratings.

## Phase 2 — Simple filters

- Allergy / gluten / dietary-restriction filters applied on top of the
  similarity search.
- Basic rating mechanism (structure TBD).

## Phase 3 — Combined scoring

- Ranking becomes a combined score: embedding similarity + nutritional
  equivalence (calories, protein, etc.), not similarity alone.

## Phase 4 — User accounts

- Optional user accounts.
- Favorite recipes.

## Phase 5 — Content and engagement

- Tutorial videos.
- Carbon-footprint awareness page.
- Comments.

## Phase 6 — Vegan extension

- Vegan alternatives (not just vegetarian).
- Larger-scale recipe sourcing (beyond manual admin CLI entry).

---

**Rule:** do not implement features from a later phase while working in an
earlier one, unless explicitly requested by the user.
