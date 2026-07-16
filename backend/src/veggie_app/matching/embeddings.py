"""Text-to-embedding conversion.

Uses sentence-transformers with a multilingual model (see
docs/ARCHITECTURE.md) so French recipe/query text embeds meaningfully.
Callers (services/) only depend on this module's function signatures, so a
future model swap won't touch routes or services.
"""

from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIM = 384


def build_query_text(title: str, ingredients: list[str]) -> str:
    return " ".join([title, *ingredients])


@lru_cache(maxsize=1)
def _get_model() -> "SentenceTransformer":
    # Imported lazily (not at module level): importing sentence_transformers
    # pulls in PyTorch, which most tests never need (they only need
    # EMBEDDING_DIM, or stub embed_text() entirely) — deferring it here keeps
    # the rest of the test suite fast and only pays the cost on first real use.
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def embed_text(text: str) -> list[float]:
    return _get_model().encode(text, normalize_embeddings=True).tolist()
