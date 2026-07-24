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
- Admin (project owner) can see the list of every recipe with the title, and with some ux he can click on it and see the details, and also edit it (modify details, title, delete, etc)

## Phase 2 — Simple filters


- First implementation of the similarity search.
- Allergy / gluten / dietary-restriction filters applied on top of the
  similarity search.
- Ranking becomes a combined score: embedding similarity + nutritional
  equivalence (calories, protein, etc.), not similarity alone, could for instance use knowns replacement for meats (tofu, seitan, tsp,..)


## Phase 3 — Combined scoring + frontend amelioration


- Improving the frontend with cool animations using anime.js, with 3d animations and cool ui tools.

## Phase 4 — User accounts

- Optional user accounts, allowing to save personal allergens, diet preferences, favorite recipes.

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
