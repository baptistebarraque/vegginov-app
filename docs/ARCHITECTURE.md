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

---

## Per-portion nutrition: calories + price tier stored, protein density computed

Date: 2026-08-02
Context: the admin wanted to record more nutrition on a recipe — calories and
protein per portion — plus a coarse cost indicator, and to surface protein
"density". `protein_grams` already existed but without a per-portion meaning.
Decision:
- **`protein_grams` is defined as per portion** (relabeled in the CLI/web
  form, not duplicated). A new `calories_per_portion` (`Float`) joins it; all
  nutrition figures are per portion, independent of `servings`, so they don't
  have to be recomputed when servings change.
- **`price_tier` is a 1..3 integer** (`MAX_PRICE_TIER`), validated in
  `recipe_service.validate_price_tier` and rendered as €/€€/€€€ in the UI —
  an ordinal cost band, not a currency amount, so it stays sortable and
  locale-free in the database.
- **Protein density is derived, never stored**: `compute_protein_density`
  returns grams of protein per 100 kcal and is computed on read in every
  response (create/get/suggestions). Calories and protein stay the single
  source of truth, so an edit to one can't leave a stored density stale. It is
  therefore also absent from the CSV import/export format, which only carries
  stored columns.
Alternatives considered: storing `protein_density` as a column (rejected —
invites drift the moment calories or protein is edited without recomputing);
adding a separate per-portion protein column beside the existing one
(rejected — two overlapping fields, the old one's meaning still undefined);
storing price as a currency amount (rejected — over-precise for a POC and
drags in currency/locale concerns; a 3-band tier is what the UI needs);
pulling full macros (carbs/fat/fibre) forward (deferred — that is the
nutritional-scoring work `docs/ROADMAP.md` places in a later phase).

---

## User accounts (Phase 4, M1): admin_sessions renamed, email reset deferred

Date: 2026-08-03
Context: Phase 4 extends the admin-only auth from `docs/ARCHITECTURE.md`'s
"Admin auth" entry to general (optional) user accounts — the reuse that
entry explicitly designed for. Two decisions fell out of that extension.
Decision:
- **`admin_sessions` renamed to `user_sessions`** (model `AdminSession` →
  `UserSession`, migration `a661cd964978` uses `op.rename_table` so existing
  sessions survive, not drop+recreate). The table was never admin-specific
  at the schema level — only `require_admin`'s extra `is_admin` check was —
  so keeping the old name once regular users log in through it too would be
  actively misleading. `require_admin` is now `require_user` (any valid
  session) plus an `is_admin` check layered on top via
  `Depends(require_user)`, instead of duplicating the cookie/session-lookup
  logic.
- **Every new `user_id` FK uses `ondelete="CASCADE"`** (`user_sessions`,
  `password_reset_tokens`, and every M2–M4 table planned after this one) —
  deleting an account must not leave orphan rows or fail on a DB constraint.
  `auth_service.register_user`/`update_account` wrap their insert/update in
  `db.begin_nested()` (a SAVEPOINT) rather than catching `IntegrityError`
  and calling the bare session `db.rollback()` — the latter unwinds the
  *entire* transaction, not just the failed statement, which is fragile the
  moment a caller does other work in the same session first (and broke the
  test fixture's own transaction bookkeeping in practice — see
  `join_transaction_mode="create_savepoint"` in `backend/tests/conftest.py`).
- **Password reset has no real email delivery yet**: there is no
  SMTP/mail dependency anywhere in this project (same "add it when actually
  needed" reasoning as the embeddings model and image storage choices).
  `POST /auth/password-reset/request` generates a token exactly like a
  login session (sha256-hashed at rest, 1h expiry, single-use, deleted on
  consumption) but returns the raw token/link directly in the JSON response
  instead of emailing it; the frontend just displays it inline. This is a
  **known gap that must close before any real deployment** — email
  enumeration is already guarded (the endpoint always returns 200), but
  handing the token to whoever asked for it, instead of only the account
  owner's inbox, is a placeholder, not a security-reviewed design.
Alternatives considered: drop-and-recreate the sessions table under the new
name (rejected — needlessly logs out every admin session on deploy for no
benefit, `rename_table` is just as easy); adding SMTP now (rejected per
explicit user decision — no mail infra exists yet and this app has no other
external-service dependency to justify adding one before it's load-bearing);
catching `IntegrityError` with a plain `db.rollback()` (rejected after it
surfaced a SAWarning in tests — see above).

---

## User preferences (Phase 4, M2): optional auth, hard allergen exclusion only

Date: 2026-08-04
Context: Phase 4's preference profile (calorie orientation, diet, allergens,
price range) needs to apply to `/suggestions` — a public, previously fully
anonymous endpoint — without making accounts stop being optional.
Decision:
- **`GET`/`PUT /preferences`** are the only account-gated routes here (both
  `require_user`, any role). One row per user in `user_preferences`
  (`models/user_preference.py`), created lazily on first `PUT` rather than
  at signup — matches "optional" all the way down, no empty row created
  just because someone made an account.
- **Enum values are plain strings validated in `preference_service.py`**
  (`calorie_orientation`: `low`/`balanced`/`high`; `diet`: `omnivore`/
  `vegetarian`/`pescatarian`/`vegan`), not a Postgres `ENUM` type — matches
  how `protein_source`/`price_tier` are already validated in
  `recipe_service.py` (Python-level check, plain column) rather than
  introducing a second validation mechanism. `price_range` reuses the
  existing recipes `price_tier` 1..3 scale directly instead of a new one.
  `allergens` stays free-form text (`ARRAY(String)`), matching
  `Recipe.allergens` — recipes don't constrain allergens to a fixed
  vocabulary either, so a preference dropdown would just invent a list nothing
  else on the backend recognizes.
- **`/suggestions` gained *optional* auth**: `auth_service.get_optional_user`
  reads the session cookie if present and returns `None` instead of raising
  401 when it's missing or invalid, unlike `require_user`. The route applies
  the caller's saved allergen list only when logged in and
  `ignore_preferences` (new `SuggestionRequest` field) is false; anonymous
  requests are completely unaffected. `api/suggestions.ts` on the frontend
  had to start sending `credentials: "include"` for this to reach the
  backend at all — it didn't before, since the endpoint had no session
  concept until now.
- **Allergens are the only preference actually applied to ranking**, and as
  a hard pre-ranking exclusion (`recipe_service.get_suggestions`'
  `excluded_allergens` filters the candidate list before `rank_candidates`
  runs), never a soft down-rank — this is the literal rule in the GitHub
  issue driving Phase 4. Diet and calorie orientation are stored but not yet
  read by ranking; wiring them in is a scoring-design decision (how to blend
  a soft preference into the existing similarity/protein fusion score)
  deliberately deferred rather than bolted on ad hoc here.
Alternatives considered: a Postgres `ENUM` type for calorie_orientation/diet
(rejected — inconsistent with the existing `protein_source`/`price_tier`
validation style, and harder to extend without a migration if the vocabulary
grows); requiring login for `/suggestions` when preferences should apply
(rejected — breaks "optional accounts" for the one endpoint that matters
most); soft-weighting allergens instead of excluding (rejected — contradicts
the issue's explicit "hidden or explicitly flagged, never silently ranked
lower" rule).

## Price budget (hard filter) + calorie orientation (soft nudge) in ranking

Date: 2026-08-04
Context: Following the M2 entry above, which stored `price_range` and
`calorie_orientation` but left them unread by ranking, `/suggestions` now
applies both. They are treated differently on purpose — the two preferences
are different *kinds* of constraint.
Decision:
- **Price is a hard pre-ranking filter**, alongside the allergen exclusion in
  `recipe_service.get_suggestions`. A recipe is kept when
  `price_tier <= max_price_tier`; a recipe priced above the budget is dropped
  outright (a budget must not be silently overspent), matching the allergen
  filter's "exclude, never down-rank" shape. Two deliberate edge cases:
  - `max_price_tier == MAX_PRICE_TIER` (€€€) is **indifferent** — every recipe
    fits the top tier — so the filter pass is skipped entirely there.
  - Recipes with **no `price_tier` yet are kept**, not dropped, so results
    don't collapse while the price/CIQUAL backfill is still in progress. Once
    every recipe is priced this could be tightened to exclude unknowns.
- **Calorie orientation is a soft ranking nudge**, not a filter — calories are
  a continuum and a strong taste match sitting just over a bucket boundary
  shouldn't be pruned. It lives in the pure `matching/` layer:
  `matching/nutrition_view.py`'s `calorie_orientation_score` buckets a recipe's
  `calories_per_portion` (`< LOW_MAX` low, `> HIGH_MIN` high, else balanced)
  and scores the match 1.0 / 0.5 / 0.0 for same / adjacent / opposite bucket.
  `matching/fusion.py` blends it onto the title+ingredients similarity with a
  small `CALORIE_WEIGHT` (0.15) so similarity stays dominant and the nudge
  mostly breaks ties. Bucket thresholds and the weight are module constants,
  tunable once real nutrition data and judged pairs exist.
- **Both terms are a strict superset of prior behavior.** When
  `calorie_orientation is None`, `fusion.apply_calorie_orientation` returns the
  similarity untouched (not a neutral-blended value), so anonymous and
  indifferent users get byte-identical scores and ordering. A recipe with no
  `calories_per_portion` scores the neutral 0.5 rather than 0, so un-populated
  recipes aren't buried. The route reads `price_range`/`calorie_orientation`
  from the caller's saved preferences under the same `ignore_preferences` gate
  as allergens.
- **No migration**: `recipes.price_tier`/`calories_per_portion` and
  `user_preferences.price_range`/`calorie_orientation` all already existed
  (M2) — this change is ranking logic only. Populating `calories_per_portion`
  from the CIQUAL database is a separate data track; until then the calorie
  nudge scores everything neutral and the price filter only bites on
  already-priced recipes.
Alternatives considered: making calorie orientation a hard bucket filter
(rejected — over-prunes strong taste matches and risks empty results while
calorie data is sparse; user chose the soft nudge); excluding unpriced recipes
under a budget (rejected for now — same sparse-data risk; user chose lenient);
folding the calorie term into the existing title/ingredient `fuse_scores`
weights (rejected — keeping it a second-level blend leaves the title/ingredient
weighting untouched and independently tunable).

---

## Watchlist (Phase 4, M3): idempotent add/remove, is_watchlisted computed per request

Date: 2026-08-04
Context: the "save for later" watchlist (`docs/ROADMAP.md` Phase 4, GitHub
issue section 3) needed add/remove/list plus a way for recipe cards to show
saved state, without adding a second round-trip per card.
Decision:
- **One row per (user, recipe)** in `watchlist_entries`
  (`models/watchlist_entry.py`), unique on `(user_id, recipe_id)`, both FKs
  `ondelete="CASCADE"` (same rule as every M1–M2 table: deleting an account
  or a recipe must not orphan rows or hit a DB constraint).
- **Add and remove are idempotent**, not strict create-once/delete-once:
  saving an already-saved recipe returns the existing entry instead of
  raising or duplicating; removing an absent entry is a silent no-op
  (`watchlist_service.add`/`remove`). This matches the frontend's single
  toggle button — a double-click or a stale UI state should never surface an
  error, since the end state ("saved" or "not saved") is unambiguous either
  way. `DELETE /watchlist/{recipe_id}` returns `204` unconditionally for the
  same reason.
- **`list_for_user` orders by `id DESC`, not `created_at DESC`**: within one
  Postgres transaction `now()` is frozen at transaction start, so entries
  added back-to-back in the same transaction (as the test suite does) tie on
  `created_at` and sort arbitrarily. `id` is monotonic per insert regardless
  of transaction timing, so it's the correct tiebreak — caught by a failing
  test (`test_list_for_user_orders_most_recent_first`), not by inspection.
- **`RecipeSuggestion.is_watchlisted`** is computed once per `/suggestions`
  call (`watchlist_service.watchlisted_recipe_ids` — one query for every
  candidate recipe's membership, not one query per recipe) rather than the
  frontend making a second request per card. Defaults to `false` for
  anonymous callers, mirroring `get_optional_user`'s existing optional-auth
  shape from M2. `RecipeResponse` (the admin create/edit/detail shape) does
  **not** get this field — an admin editing a recipe isn't the "browse and
  save for later" flow the issue describes, so it would be a field with no
  real UI use there.
- **Frontend**: `WatchlistButton` renders as a DOM *sibling* of
  `RecipeSuggestionCard`'s button, not nested inside it — two interactive
  elements can't nest in valid HTML, and the card's whole surface is already
  a `<button>` that opens the detail panel on click/hover.
Alternatives considered: raising a 409 on duplicate add / 404 on double
remove (rejected — turns a harmless double-click into a surfaced error the
frontend would have to swallow anyway); a separate `GET
/watchlist/{recipe_id}/status` endpoint for card state (rejected — exactly
the N+1-per-card round trip `is_watchlisted` avoids); storing
`is_watchlisted` on `RecipeResponse` too (rejected — no admin-flow use for
it, see above).

## Likes (Phase 4, M4): public counter, private liked-list, count computed on ranked recipes only

Date: 2026-08-06
Context: the like system (`docs/ROADMAP.md` Phase 4, GitHub issue section 4)
needed like/unlike, a per-recipe like *counter*, and a "liked recipes" view —
the first M4 feature where a piece of the state (the count) is **public**,
unlike the fully-private watchlist.
Decision:
- **Structural twin of the watchlist** where the shapes match: one row per
  `(user, recipe)` in `recipe_likes` (`models/recipe_like.py`), unique on
  `(user_id, recipe_id)`, both FKs `ondelete="CASCADE"`; idempotent
  `add`/`remove` (`like_service`); `list_for_user` ordered by `id DESC` for
  the same frozen-`now()` tiebreak reason documented under Watchlist above.
  The like row carries no `notes`/`planned_for` — a like is a bare marker.
- **The count is public, so it lives on `/suggestions`, not on the
  `require_user` `/likes` routes.** `RecipeSuggestion` gains `like_count`
  (total across all users, shown to everyone including anonymous callers) and
  `is_liked` (this user's flag, `false` for anonymous — same optional-auth
  shape as `is_watchlisted`). `like_count` is computed **inside
  `get_suggestions`, over the 4 *ranked* recipe ids only** via one grouped
  query (`like_service.like_counts`), not per recipe and not over the whole
  candidate set — the ranking already narrowed it to `SUGGESTION_COUNT`.
  `is_liked` is threaded in from the route like `is_watchlisted`.
- **`recipe_service` calls `like_service`** for the count. Services calling
  services is already the norm here (`recipe_service` uses `image_service`);
  the count depends on the ranked ids, which only exist inside
  `get_suggestions`, so pushing the query up to the route would mean the route
  guessing which recipes will rank.
- **`POST`/`DELETE /likes/{recipe_id}` return the authoritative
  `{recipe_id, like_count, is_liked}`** (`LikeStatusResponse`), and `DELETE`
  is `200`, not `204` like the watchlist's. The count is shared state that
  other users mutate concurrently, so the frontend reconciles its optimistic
  ±1 against the server's real number rather than trusting its own guess —
  a `204` would force a second fetch to get it.
- **Frontend places the heart in the detail panel only**, not on the cards
  (which already carry the watchlist bookmark) — keeps the 2×2 grid
  uncluttered. Because the count is public, `LikeButton` renders for anonymous
  visitors too (unlike `WatchlistButton`, which is omitted when anonymous);
  their click is routed to `/login` by `HomePage`.
Alternatives considered: a dedicated `GET /likes/count/{recipe_id}` per card
(rejected — the same N+1 the suggestion-embedded count avoids); computing the
count over every candidate recipe before ranking (rejected — wasted work on
recipes that won't be shown); `DELETE` returning `204` for watchlist parity
(rejected — the count is concurrently-mutable, see above); reusing the word
"favoris" for the UI label (rejected — it's already loosely used for the
watchlist, so likes use "Coups de cœur" to stay distinct).

---

## Admin users view: read-only, aggregated counts, `/admin` becomes a hub

Date: 2026-09-01
Context: the admin could see every recipe but had no way to see who had signed
up. With Phase 4 accounts in place (preferences, watchlist, likes), the admin
needed a view of the accounts and what each one saved.
Decision:
- **No schema change.** The view only reads `users`, `user_preferences`,
  `watchlist_entries` and `recipe_likes` — no new table, no migration. What the
  admin sees is derived from rows those features already write.
- `GET /admin/users` (`AdminUserListItem`: email, role, signup date, watchlist
  and like counts, a `has_preferences` flag) and `GET /admin/users/{user_id}`
  (`AdminUserDetail`: the same fields plus the preference profile, the
  watchlist entries and the liked recipes), both behind the same
  `require_admin` dependency as `/admin/recipes`. New router module rather than
  more endpoints in `admin_recipes.py`, which is already multipart/image-shaped
  and has nothing to do with accounts.
- **Read-only on purpose**, and `password_hash` is never in a response — a test
  asserts the string doesn't appear in the list payload. Account changes stay
  in `/auth/account`, where they are the owner's own action; an admin editing
  or deleting someone else's account is a bigger decision (audit trail,
  self-demotion guards) than this view needs to make.
- **`user_admin_service` aggregates the counts with one grouped query per
  relation** (`GROUP BY user_id`), so listing N accounts is 4 queries, not
  1 + 3N — the same batching reasoning as `like_service.like_counts`. The
  detail path instead reuses `preference_service` / `watchlist_service` /
  `like_service` unchanged: for a single user there is nothing to batch.
- Listing is ordered by `id DESC` (newest account first), not `created_at` —
  within one transaction Postgres freezes `now()`, so accounts inserted
  back-to-back in a test tie on `created_at`. Same reasoning as
  `watchlist_service.list_for_user`.
- **Frontend: `/admin` becomes a hub** ("Recettes" / "Utilisateurs" cards with
  live counts) and the add-recipe form moves to `/admin/recipes/new`, declared
  before `/admin/recipes/:id` so "new" isn't parsed as a recipe id. The recipe
  section is otherwise untouched. `AdminUsersTable` is a separate component
  from `AdminTable` rather than a generalisation of it — `AdminTable` owns the
  delete/confirm flow, which has no counterpart in a read-only view.
Alternatives considered: adding the users endpoints to `admin_recipes.py`
(rejected — unrelated concern, and that module is multipart-specific); a
`GET /admin/users?include=preferences` single endpoint (rejected — the list
would carry every user's full watchlist just to render a table of counts, the
same wasted payload `RecipeListItem` avoids); keeping `/admin` as the
add-recipe page with a second link (rejected — the admin now has two real
sections, and a form is a poor landing page for choosing between them);
per-user `COUNT` subqueries in the list query (rejected — N+1 as the account
count grows).
