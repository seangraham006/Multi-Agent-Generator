"""Generate vector embeddings for memory content."""

from __future__ import annotations

import logging

from sentence_transformers import SentenceTransformer

from app.config import EMBEDDING_MODEL

logger = logging.getLogger(__name__)

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    """Lazy-load and cache the embedding model."""
    global _model
    if _model is None:
        logger.info("Loading embedding model '%s' …", EMBEDDING_MODEL)
        _model = SentenceTransformer(EMBEDDING_MODEL)
        logger.info("Embedding model loaded.")
    return _model


def generate_embedding(text: str) -> list[float]:
    """Return a normalised embedding vector for *text*."""
    model = get_model()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()
