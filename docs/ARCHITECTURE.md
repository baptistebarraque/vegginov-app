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
