# Architecture decisions

Non-trivial architecture decisions get one entry here, in the order they were
made. This is a log, not a design spec — keep entries short and dated.

Template for a new entry:

```
## <short title>

Date: YYYY-MM-DD
Context: why this decision was needed.
Decision: what was chosen.
Alternatives considered: what else was on the table and why it was rejected.
```

---

## Embedding dimension fixed at 384

Date: 2026-07-13
Context: the `recipes.embedding` column (`pgvector`) requires a fixed
dimension at migration time, but the actual embedding model isn't wired up
until a later step (`matching/embeddings.py`). Changing the dimension later
requires a new migration and re-embedding every stored recipe, so it's worth
deciding deliberately now rather than drifting into a value.
Decision: 384 dimensions, matching `paraphrase-multilingual-MiniLM-L12-v2`
(sentence-transformers). Good multilingual/French support, fast, small
model — a reasonable default for a POC.
Alternatives considered: `distiluse-base-multilingual-cased-v2` (512-dim)
and `paraphrase-multilingual-mpnet-base-v2` (768-dim) — both higher quality
but slower and heavier; not justified before the POC needs to prove out
similarity quality first.

---

## torch pinned to the CPU-only wheel index

Date: 2026-07-15
Context: wiring in real `sentence-transformers` embeddings (Step 10) pulls
in `torch` as a dependency. On Linux — both the backend Docker image and
GitHub Actions CI — the default PyPI resolution for `torch` is the
CUDA-enabled build, adding ~2GB+ of unused `nvidia-*`/`cuda-*`/`triton`
packages, since this app never runs on a GPU anywhere.
Decision: pin `torch` to PyTorch's CPU-only wheel index via
`[tool.uv.sources]` / `[[tool.uv.index]]` in `backend/pyproject.toml`, and
keep `torch` listed as a *direct* dependency, not just transitive via
`sentence-transformers`. This second part is required, not cosmetic: `uv`
only honors a `tool.uv.sources` override for a package that appears as a
direct dependency — left purely transitive, the override was silently
ignored and `torch` still resolved the CUDA build with no warning. Verify
with `grep -A15 'name = "torch"' backend/uv.lock`: it should show
`source = { registry = "https://download.pytorch.org/whl/cpu" }` and no
`nvidia-*`/`cuda-*`/`triton` dependencies.
Alternatives considered: leaving `torch` transitive-only (rejected —
silently pulls the CUDA build on Linux; caught when the backend Docker
rebuild started downloading gigabytes of `nvidia-*` packages); accepting
the CUDA build as-is (rejected — wasted disk/bandwidth/build time for a
POC with no GPU usage anywhere, and the same cost would hit every CI run).

---

## Admin auth: DB-backed sessions, not JWT

Date: 2026-07-16
Context: the admin web interface (login + recipe upload) needs real
authentication, deliberately built to be reusable when phase 4 adds general
user accounts, not a one-off admin-only hack.
Decision:
- Credentials live on the existing, previously-unused `User` model
  (`password_hash` + `is_admin`), not a separate throwaway admin table —
  phase 4 builds on the same table instead of migrating away from one.
- Sessions are opaque random tokens (`secrets.token_urlsafe`), stored
  server-side in `admin_sessions` as a *sha256 hash* of the token (same
  reasoning as password hashing — a DB leak alone shouldn't hand out valid
  sessions), sent to the browser as an httpOnly cookie. Not JWT: simpler to
  revoke (delete the row; a JWT lives until it expires, no server-side kill
  switch without extra infrastructure), and there's exactly one first-party
  frontend, so JWT's main benefit (stateless verification across
  independent services) doesn't apply.
- Cookie is `secure=False` — correct for local dev over `http://localhost`,
  but this **must become `True`** before any real HTTPS deployment, or
  browsers will still send it over plain HTTP.
- No CSRF token scheme: `SameSite=Lax` already blocks the cookie on
  cross-site POST requests, covering the realistic risk for a single-admin
  POC. Revisit if/when phase 4 adds more sensitive authenticated actions.
Alternatives considered: JWT stored client-side (rejected — no clean
revocation, and the statelessness benefit needs multiple independent
verifying services to matter, which this app doesn't have); a separate
`Admin` table isolated from future user accounts (rejected — phase 4 would
need its own separate table with no reuse of this work); full CSRF-token
middleware (rejected as over-engineering at this scope, given `SameSite=Lax`
already covers the main attack path).

---

## Ingredients view + Title view fusion

Date: 2026-07-26
Context: Phase 2's "first implementation of the similarity search" replaces
the Phase 1 POC's single whole-recipe embedding (title + ingredient names,
one cosine-similarity ranking) with a multi-view score, per the recipe-
matching design notes. A raw embedding over the full ingredient vocabulary
conflates "what gets cooked together" with "what plays the same role as",
which isn't what similarity should mean here.
Decision:
- **Ingredients view** (`matching/ingredients_view.py`): a protein sub-score
  (`matching/substitution.py`, a hand-curated meat/fish -> vegetarian
  substitution table — a small closed problem, more reliable here than an
  embedding trained for ingredient co-occurrence) and a non-protein
  sub-score (`matching/ingredient_similarity.py`, FlavorGraph embeddings +
  the Hungarian algorithm for optimal ingredient-to-ingredient matching),
  combined with a fixed `protein_weight` (0.4, arbitrary starting point).
  A candidate recipe's protein is read directly from its (now
  dropdown-constrained) `protein_source` field; a user's query has no such
  field, so its protein-like word(s) are detected from the raw ingredient
  list against the substitution table's vocabulary instead
  (`split_query_ingredients_by_role`).
- **Title view** (`matching/embeddings.py`): `Recipe.embedding` now stores a
  **title-only** sentence-transformers embedding, not title + ingredients —
  ingredient-based similarity moved entirely to the Ingredients view above,
  so folding ingredient text into this embedding too would double-count it
  with a much cruder signal. Existing rows were recomputed once via
  `backend/scripts/recompute_title_embeddings.py` (safe to re-run).
- **Fusion** (`matching/fusion.py`): `fuse_scores` combines the two views
  with a fixed `title_weight` (0.3, arbitrary starting point) into the
  score `get_suggestions` ranks candidates by.
- FlavorGraph's data files are a manually-downloaded, gitignored asset
  (~10MB, not committed — see `backend/data/flavorgraph/README.md`), absent
  in CI and on a fresh clone. `flavorgraph.get_vector` catches their absence
  and returns `None` rather than raising, so a missing dataset degrades the
  Ingredients view's non-protein sub-score to 0 instead of crashing every
  suggestion request.
Alternatives considered: a second `title_embedding` column alongside the
existing one (rejected — the old title+ingredients embedding has no
remaining use once the Ingredients view exists, so keeping it around would
just be dead weight); computing the two weights via logistic regression
from the start (rejected — no manually judged pairs exist yet to train on;
fixed weights are the documented starting point in the design notes,
section 6.2, revisit once ~150-300 judged pairs exist).

---

## Recipe image storage: local disk, bind-mounted

Date: 2026-07-24
Context: the admin recipe form gained an optional image upload (alongside
optional protein info and step-by-step instructions). Needed a place to
store the file and a way to serve it back to the frontend, without adding
a paid external dependency (same reasoning as the embeddings model choice).
Decision: images are saved to `settings.upload_dir` (`backend/uploads/`,
`services/image_service.py`), validated by extension (`.png`/`.jpg`/`.jpeg`)
and a 5MB size cap, under a generated `uuid4` filename — the `Recipe` table
stores only that filename (`image_filename`), never the original one.
Served back via a FastAPI `StaticFiles` mount at `/media`. `docker-compose.yml`
uses a **bind mount** (`./backend/uploads:/app/uploads`), not a named
volume, so images saved by the Dockerized backend (web upload) and images
saved by the CLI running locally via `uv run` (same relative `uploads`
path, different physical process) land in the same place — a named volume
would only be visible to the container, splitting the two admin entry
points across two different storage locations. This only works because the
deployment target is a VPS/self-hosted Docker host with a persistent disk,
confirmed explicitly when this was designed; it would need to change to
object storage (S3-compatible) if the target ever becomes a
serverless/ephemeral-filesystem platform.
Alternatives considered: base64-encoded bytes in the `recipes` row
(rejected — bloats every row and every `/suggestions` query payload with
image data that's only needed on the admin/recipe-detail path); cloud
object storage (rejected for now — adds cost/complexity and an external
dependency before the POC needs it; revisit if the deployment target
changes).

---

## Bulk recipe import: CSV, all-or-nothing, semicolon sub-delimiter

Date: 2026-07-24
Context: adding recipes one at a time (CLI or the admin web form) doesn't
scale once the admin has many recipes ready at once. Needed a bulk path
without inventing a new file format or adding a parsing dependency.
Decision:
- **CSV via the admin web UI** (`POST /admin/recipes/import`, admin-only,
  same session auth as the single-recipe route), not a CLI script — the
  admin already has a point-and-click web upload flow; bulk import extends
  that instead of adding a second, inconsistent entry point. Parsing uses
  Python's stdlib `csv` module — no new dependency.
- **Columns** mirror the single-recipe fields exactly: `title`,
  `ingredients` (required), `allergens`, `prep_time_minutes`, `servings`,
  `protein_source`, `protein_grams`, `instructions` (optional). No image
  column — a CSV cell can't hold binary image data; images stay a
  per-recipe follow-up via the existing single-recipe form.
- **List-valued cells** (`ingredients`/`allergens`/`instructions`) use a
  **semicolon** as the in-cell delimiter (e.g. `lentilles corail; lait de
  coco; curry`), since commas are already the CSV column separator.
- **All-or-nothing**: every row is validated (`recipe_import_service.
  parse_csv`) *before* any database write. If any row is invalid, nothing
  is imported and every invalid row's error is returned (not just the
  first), so the admin fixes the CSV once and re-uploads, instead of
  ending up with a partially-imported batch that's hard to dedupe on
  retry. Enforced structurally, not by a manual rollback: parsing is a
  pure function with no DB access, and the route only calls `db.commit()`
  once, after every row's `recipe_service.create_recipe` call has
  succeeded — an exception anywhere in that loop propagates past the
  commit, and `get_db`'s `session.close()` discards the uncommitted work.
Alternatives considered: best-effort import (commit valid rows, report
failures) — rejected because fixing errors and re-uploading the same file
would re-create the rows that already succeeded, with no natural
duplicate-detection to fall back on at this POC stage; a separate CLI
bulk-import command — rejected for now, no immediate need beyond the web
flow the admin already uses.

**CSV export** (`GET /admin/recipes/export`, admin-only; download button on
the admin recipe-list page) is the inverse of import:
`recipe_import_service.export_recipes_to_csv` serializes every recipe with the
same columns and semicolon sub-delimiter `parse_csv` accepts, so a downloaded
file round-trips back through import unchanged (verified by a round-trip test).
Export and import share the column list and delimiter constants in one module
so the two formats can't drift apart. Images are omitted, matching import. A
UTF-8 BOM is prepended so spreadsheet apps render accented French correctly;
`parse_csv` reads with `utf-8-sig`, so the BOM is stripped on re-upload.

---

## Ingredients become structured {name, quantity}, required when servings is set

Date: 2026-07-24
Context: a recipe that states "serves 4" is only useful if each ingredient
also says how much of it is needed at that serving size — plain ingredient
names (the original `ARRAY(String)` column) can't carry that.
Decision:
- `recipes.ingredients` changed from `text[]` to a `json` column of
  `{"name": str, "quantity": str | None}` objects (`IngredientEntry` in
  `models/recipe.py`, `IngredientEntrySchema` in `schemas/recipe.py`).
  Quantity is a free-text string (`"200g"`, `"1 c.a.s"`, `"20cl"`...), not
  a numeric amount + unit enum — recipe quantities don't share one unit
  system, and forcing one would either reject valid input or need an
  unbounded unit list.
- Migration `be16d5b1145d` converts existing rows in place (`UPDATE ...
  json_agg(json_build_object(...))` over the old array), setting
  `quantity: null` for every pre-existing ingredient rather than dropping
  or guessing at the data.
- **Enforcement lives in one place**: `recipe_service.
  validate_ingredient_quantities(ingredients, servings)` raises
  `IngredientQuantityError` if `servings` is set and any ingredient has no
  quantity; every entry point (`create_recipe` itself, plus
  `recipe_import_service._parse_row` for CSV rows) calls it, so the rule
  can't be bypassed by adding a new admin entry point later without also
  wiring this in. When `servings` is left blank, quantity stays fully
  optional, matching the CSV/CLI's existing "optional fields can be
  skipped" convention.
- **Wire format**: the admin route's `ingredients` field switched from
  repeated multipart form fields (one per name) to a single JSON-encoded
  string field, validated with `pydantic.TypeAdapter(list
  [IngredientEntrySchema])` — multipart's flat key-value fields can't
  express `{name, quantity}` pairs as a repeated list the way plain
  strings (allergens/instructions) can. The CSV format instead extends the
  existing semicolon-separated cell with a second delimiter: `riz:200g;
  curry` (colon between name and quantity, quantity optional per item).
- The public `/suggestions` endpoint and `RecipeSuggestion.ingredients`
  are unaffected (still plain `list[str]`) — quantity is an admin/creation
  concern, not something end users searching for suggestions submit or
  need to see.
Alternatives considered: inline free-text ("200g de riz" as the whole
ingredient string, no schema change) — rejected because quantity
wouldn't be a separately usable field (e.g. for a future "scale this
recipe" feature); numeric amount + fixed unit dropdown — rejected, see
above; validating in the API route instead of `recipe_service` — rejected
because the CLI and CSV import don't go through the route, and the rule
needs to hold for every way a recipe gets created.

---

## Admin recipe list/detail/edit/delete

Date: 2026-07-24
Context: closing out the last Phase 1 item — the admin needed a way to see
every recipe, open one, edit it, and delete it, not just add new ones.
Decision:
- `GET /admin/recipes` (title + thumbnail only, `RecipeListItem`) and
  `GET /admin/recipes/{id}` (full detail, `RecipeResponse`) added alongside
  the existing `POST`. `PUT /admin/recipes/{id}` and
  `DELETE /admin/recipes/{id}` round out the CRUD set — all admin-only,
  same session auth as every other `/admin/*` route.
- `CreateRecipeResponse` renamed to `RecipeResponse`: once `GET`/`PUT` also
  return this exact shape, a name starting with "Create" would be actively
  misleading, not just imprecise.
- **Update always recomputes the embedding** from the (possibly changed)
  title/ingredient names — an edited recipe with a stale embedding would
  quietly stop matching what it should in `/suggestions`. Both `create_
  recipe` and `update_recipe` go through the same `_prepare_embedding`
  helper (validates quantities, then embeds) so this can't drift between
  the two code paths.
- **Image lifecycle on edit/delete**: replacing an image deletes the old
  file (`image_service.delete_recipe_image`) after the new one saves
  successfully, not before — an upload failure leaves the original image
  intact instead of the recipe briefly having none. A `remove_image` form
  flag lets the admin clear an image without uploading a replacement.
  Deleting a recipe deletes its image file too, so `backend/uploads/`
  doesn't accumulate orphaned files with no owning row.
- **Frontend**: `AdminRecipeForm` gained optional `initialValues`/
  `existingImageUrl`/`submitLabel`/`loadingLabel` props so the same form
  drives both "add" (`AdminUploadPage`) and "edit" (`AdminRecipeDetailPage`)
  — one validation/UX implementation, not two. `onSubmit` gained a second
  `removeExistingImage` argument the create flow simply ignores (TS allows
  a callback with fewer declared params than the type expects).
Alternatives considered: a single `RecipeResponse`-shaped list endpoint
(rejected — sends every recipe's full ingredients/instructions just to
render a title list, wasted payload as the recipe count grows); deleting
the old image file before saving the new one (rejected — a failed upload
would leave the recipe with no image at all instead of keeping the
original); a separate edit-only form component (rejected — would duplicate
every field and the quantity-required-with-servings UX rule).

---

## Frontend design system: tokens in CSS, framer-motion as the only animator

Date: 2026-08-01
Context: the first real visual pass (docs/FRONTEND.md, the "potager de nuit"
dark theme) needed a single home for design tokens and one animation engine,
across public + admin screens, without scattering hex values or stacking two
animation libraries.
Decision:
- **Tokens live in `frontend/src/index.css`** as the single source of truth.
  Colour/font/radius sit inside Tailwind v4's `@theme` block so they both
  emit as CSS custom properties *and* generate utilities (`bg-nuit`,
  `text-craie`, `font-display`, `rounded-lg`). Motion tokens (`--dur-*`,
  `--ease-*`) sit in a plain `:root` block because they are consumed by raw
  CSS transitions, not Tailwind utilities. This is Tailwind v4's `@theme`
  mechanism, not a `tailwind.config.js` — the repo is on Tailwind v4, and the
  brief forbids migrating versions in this pass. No hex value may appear in
  any component; a hardcoded colour outside `index.css` is a bug.
- **framer-motion is the only animation engine** (already in the stack
  table). Its `layout` FLIP already drives the results-grid corner-grow
  resize, and Phase 3 will lean on the same primitive, so adding a second
  library (anime.js/GSAP) would mean two engines fighting over the same
  transforms. Motion token values are mirrored once as JS constants in
  `src/utils/motion.ts` (seconds + cubic-bezier arrays framer needs) rather
  than re-read from CSS at runtime.
- **Reduced motion is honoured in one place**: a `<MotionConfig
  reducedMotion="user">` at the app root plus `useReducedMotion` in the few
  components with bespoke motion, backed by a `prefers-reduced-motion` CSS
  floor in `index.css` — not a per-component opt-out.
- **Primitives are copied into `src/components/ui/`** (Button, Input, Card,
  …), never pulled from a component-registry dependency, and restyled to the
  tokens; variant logic uses `class-variance-authority`, class composition a
  `cn()` helper (`clsx` + `tailwind-merge`).
Alternatives considered: a `tailwind.config.js` `theme.extend` (rejected —
that is the Tailwind v3 mechanism; this repo is v4, where `@theme` in CSS is
the idiom); a second animation library for "richer" effects (rejected —
framer-motion v12 covers this pass and Phase 3's `layout` needs, and two
engines animating the same elements is a bug factory); reading CSS custom
properties from JS at runtime to avoid the small motion-token duplication
(rejected — over-engineered; a handful of durations/easings mirrored in one
file is cheaper and type-safe).
