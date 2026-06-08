"""
Google Gemini embedding model wrapper.
Model: models/gemini-embedding-001 — 3072-dim, production-stable.
Uses the Gemini API (already configured) — no local model download required.

Free-tier rate limit: 100 requests/minute where each text = 1 request.
The embed() method enforces per-text rate limiting with retry on 429.
"""

import time
from typing import List
from loguru import logger

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted

from config import settings

# Gemini embedding model — 3072 dimensions
_GEMINI_EMBED_MODEL = "models/gemini-embedding-001"
_EMBED_DIM = 3072

# Rate limiting: free tier = 100 requests/minute; each text = 1 request
# We target 80/minute to leave headroom, so ~0.75 s per text.
_INTER_TEXT_DELAY = 0.75   # seconds between individual embed calls
_MAX_RETRIES = 5
_RETRY_BACKOFF = 10        # base seconds to wait on 429


def _embed_single(text: str, task_type: str) -> List[float]:
    """Embed one text with retry on 429 quota errors."""
    for attempt in range(_MAX_RETRIES):
        try:
            result = genai.embed_content(
                model=_GEMINI_EMBED_MODEL,
                content=text,
                task_type=task_type,
            )
            return result["embedding"]
        except ResourceExhausted as exc:
            wait = _RETRY_BACKOFF * (attempt + 1)
            logger.warning(f"Rate limit hit (attempt {attempt + 1}/{_MAX_RETRIES}). Waiting {wait}s…")
            time.sleep(wait)
    raise RuntimeError(f"Gemini embedding failed after {_MAX_RETRIES} retries for text: {text[:60]!r}")


class EmbeddingModel:
    """Gemini gemini-embedding-001 wrapper for generating 3072-dim embeddings."""

    def __init__(self, model_name: str = None, device: str = None):
        # model_name / device kept for API compatibility; ignored — we always use Gemini
        self._configured = False

    def _ensure_configured(self):
        if not self._configured:
            genai.configure(api_key=settings.gemini_api_key)
            logger.info(f"Gemini embedding model ready: {_GEMINI_EMBED_MODEL}")
            self._configured = True

    def embed(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Embed a list of texts for document indexing.
        Embeds one text per API call with rate-limit-safe delay between calls.
        Returns list of 3072-dim float vectors.
        """
        self._ensure_configured()
        if not texts:
            return []

        all_embeddings: List[List[float]] = []
        total = len(texts)
        logger.info(f"Embedding {total} texts via Gemini API (≈{total * _INTER_TEXT_DELAY:.0f}s estimated)…")

        for idx, text in enumerate(texts):
            emb = _embed_single(text, "RETRIEVAL_DOCUMENT")
            all_embeddings.append(emb)
            if idx % 20 == 0 and idx > 0:
                logger.info(f"  Embedded {idx}/{total} texts…")
            if idx < total - 1:
                time.sleep(_INTER_TEXT_DELAY)

        logger.debug(f"Embedded {total} texts → {len(all_embeddings)} vectors (dim={_EMBED_DIM})")
        return all_embeddings

    def embed_query(self, query: str) -> List[float]:
        """Embed a single query string with RETRIEVAL_QUERY task type."""
        self._ensure_configured()
        return _embed_single(query, "RETRIEVAL_QUERY")

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        return _EMBED_DIM

    # Kept for API compat
    def _load_model(self):
        self._ensure_configured()


# Module-level singleton
_embedding_model: EmbeddingModel = None


def get_embedding_model() -> EmbeddingModel:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = EmbeddingModel()
    return _embedding_model
