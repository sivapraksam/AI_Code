"""
Lightweight keyword-overlap reranker — no model download required.

Scoring: BM25-inspired term overlap between query tokens and passage tokens,
combined with the cosine similarity score from the vector store.
This avoids HuggingFace downloads on restricted corporate networks while
still improving result ordering over pure cosine similarity.
"""

import math
import re
from typing import List, Optional
from loguru import logger

from config import settings

# Common English stop-words to exclude from overlap scoring
_STOP_WORDS = frozenset({
    "a", "an", "the", "is", "it", "in", "of", "to", "and", "or",
    "for", "on", "with", "as", "at", "by", "be", "are", "was",
    "were", "has", "have", "had", "this", "that", "from", "its",
})


def _tokenise(text: str) -> List[str]:
    """Lower-case, split on non-alphanumeric characters, remove stop-words."""
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [t for t in tokens if t not in _STOP_WORDS and len(t) > 1]


def _keyword_score(query_tokens: List[str], passage: str) -> float:
    """Dice-coefficient overlap between query tokens and passage tokens."""
    if not query_tokens:
        return 0.0
    passage_set = set(_tokenise(passage))
    query_set = set(query_tokens)
    intersection = query_set & passage_set
    union = query_set | passage_set
    return len(intersection) / len(union) if union else 0.0


class Reranker:
    """Keyword-overlap reranker (no model download required)."""

    def __init__(self, model_name: str = None):
        # model_name kept for API compatibility; not used
        pass

    def rerank(
        self,
        query: str,
        candidates: List[dict],
        top_k: Optional[int] = None,
    ) -> List[dict]:
        """
        Rerank candidate chunks using keyword overlap + cosine similarity.

        Args:
            query: The user's question.
            candidates: List of dicts from vector_store.similarity_search.
            top_k: Number of results to return after reranking.

        Returns:
            Sorted list of candidates (highest relevance first) with 'rerank_score'.
        """
        if not candidates:
            return []

        top_k = top_k or settings.reranker_top_k
        query_tokens = _tokenise(query)

        for candidate in candidates:
            kw = _keyword_score(query_tokens, candidate.get("content", ""))
            # Blend cosine similarity (distance field is 1 - cosine in ChromaDB)
            cos_sim = 1.0 - candidate.get("distance", 0.5)
            # Combined score: 60 % cosine + 40 % keyword overlap
            candidate["rerank_score"] = round(0.6 * cos_sim + 0.4 * kw, 6)

        reranked = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
        result = reranked[:top_k]

        if result:
            logger.debug(
                f"Reranked {len(candidates)} → top {len(result)} candidates. "
                f"Top rerank_score: {result[0]['rerank_score']:.4f}"
            )
        return result


# Module-level singleton
_reranker: Optional[Reranker] = None


def get_reranker() -> Reranker:
    global _reranker
    if _reranker is None:
        _reranker = Reranker()
    return _reranker
