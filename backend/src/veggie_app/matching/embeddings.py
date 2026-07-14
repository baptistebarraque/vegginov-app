"""Text-to-embedding conversion.

Stubbed for now: embed_text() returns a deterministic pseudo-random vector
seeded from a hash of the input text, so results are reproducible in tests
but carry no real semantic meaning. Will be swapped for a real
sentence-transformers model later. Callers (services/) only depend on this
module's function signatures, so that swap won't touch routes or services.
"""

import hashlib
import random

# Matches paraphrase-multilingual-MiniLM-L12-v2, the model planned for the
# real implementation (see docs/ARCHITECTURE.md).
EMBEDDING_DIM = 384


def build_query_text(title: str, ingredients: list[str]) -> str:
    return " ".join([title, *ingredients])


def embed_text(text: str) -> list[float]:
    seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)
    rng = random.Random(seed)
    return [rng.uniform(-1.0, 1.0) for _ in range(EMBEDDING_DIM)]
