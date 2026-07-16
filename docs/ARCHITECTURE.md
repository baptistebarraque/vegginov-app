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
