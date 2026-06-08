"""
RAG Pipeline Orchestrator.
Wires together: embedding → vector search → reranking → Gemini generation.
Implements escalation paths for low-confidence and jurisdiction-specific queries.
"""

from typing import List, Optional
from dataclasses import dataclass, field
from loguru import logger

from config import settings
from src.ingestion.embedder import get_embedding_model
from src.retrieval.vector_store import get_vector_store
from src.retrieval.reranker import get_reranker
from src.generation.llm_client import get_llm_client


@dataclass
class RAGResponse:
    """Structured response from the RAG pipeline."""
    question: str
    answer: str
    citations: List[str]
    retrieved_chunks: List[dict]
    confidence: str
    sources_used: int
    latency_ms: int
    model: str
    escalation_required: bool = False
    escalation_reason: str = ""
    retrieval_scores: List[float] = field(default_factory=list)


# Keywords that may indicate jurisdiction-specific questions requiring escalation
_JURISDICTION_KEYWORDS = [
    "state law", "california", "new york", "texas", "florida",
    "eu", "european", "gdpr", "uk", "england", "canada",
    "cayman", "offshore", "cross-border jurisdiction",
]

# Keywords suggesting policy boundary questions
_BOUNDARY_KEYWORDS = [
    "difference between", "vs", "versus", "which policy",
    "boundary between", "aml vs fraud", "overlap",
]

# Minimum reranker score to consider HIGH confidence
_HIGH_CONFIDENCE_THRESHOLD = 0.5


def _check_escalation_needed(
    question: str,
    confidence: str,
    top_rerank_score: float,
) -> tuple[bool, str]:
    """
    Determine if the response requires human escalation.
    Returns (escalation_required, escalation_reason).
    """
    question_lower = question.lower()

    if confidence == "LOW" or top_rerank_score < 0.2:
        return True, (
            "Low-confidence response: The retrieved documents may not fully address "
            "this question. Escalate to Compliance subject matter expert."
        )

    for kw in _JURISDICTION_KEYWORDS:
        if kw in question_lower:
            return True, (
                f"Jurisdiction-specific query detected (keyword: '{kw}'). "
                "Escalate to jurisdiction-specific legal counsel or Regulatory Affairs."
            )

    for kw in _BOUNDARY_KEYWORDS:
        if kw in question_lower:
            return True, (
                "Policy boundary query detected. "
                "Escalate to CCO for clarification of the applicable policy framework."
            )

    return False, ""


class RAGPipeline:
    """End-to-end RAG pipeline for compliance Q&A."""

    def __init__(self):
        self.embedder = get_embedding_model()
        self.vector_store = get_vector_store()
        self.reranker = get_reranker()
        self.llm = get_llm_client()

    def query(
        self,
        question: str,
        top_k_retrieval: Optional[int] = None,
        top_k_rerank: Optional[int] = None,
        document_type_filter: Optional[str] = None,
    ) -> RAGResponse:
        """
        Execute the full RAG pipeline for a compliance question.

        Pipeline steps:
          1. Embed the query using local HF model.
          2. Retrieve top_k_retrieval candidates from ChromaDB.
          3. Rerank using cross-encoder; keep top_k_rerank.
          4. Generate citation-grounded answer with Gemini.
          5. Apply escalation logic.
          6. Return structured RAGResponse.
        """
        top_k_retrieval = top_k_retrieval or settings.retrieval_top_k
        top_k_rerank = top_k_rerank or settings.reranker_top_k

        logger.info(f"RAG query: '{question[:80]}...' " if len(question) > 80 else f"RAG query: '{question}'")

        # Step 1: Embed query
        query_embedding = self.embedder.embed_query(question)

        # Step 2: Vector similarity search
        candidates = self.vector_store.similarity_search(
            query_embedding=query_embedding,
            top_k=top_k_retrieval,
            document_type_filter=document_type_filter,
        )

        if not candidates:
            logger.warning("No candidates retrieved from vector store.")
            return RAGResponse(
                question=question,
                answer=(
                    "INSUFFICIENT_CONTEXT: No relevant documents were found in the knowledge base. "
                    "Please ensure documents have been ingested. "
                    "Escalate to Compliance team."
                ),
                citations=[],
                retrieved_chunks=[],
                confidence="LOW",
                sources_used=0,
                latency_ms=0,
                model=settings.gemini_model,
                escalation_required=True,
                escalation_reason="No documents found in knowledge base.",
            )

        # Step 3: Rerank
        reranked = self.reranker.rerank(
            query=question,
            candidates=candidates,
            top_k=top_k_rerank,
        )

        top_rerank_score = reranked[0]["rerank_score"] if reranked else 0.0
        retrieval_scores = [c.get("rerank_score", 0.0) for c in reranked]

        # Step 4: Generate answer
        llm_response = self.llm.generate_answer(
            question=question,
            context_chunks=reranked,
            top_rerank_score=top_rerank_score,
        )

        # Step 5: Escalation check
        escalation_required, escalation_reason = _check_escalation_needed(
            question=question,
            confidence=llm_response["confidence"],
            top_rerank_score=top_rerank_score,
        )

        return RAGResponse(
            question=question,
            answer=llm_response["answer"],
            citations=llm_response["citations"],
            retrieved_chunks=reranked,
            confidence=llm_response["confidence"],
            sources_used=llm_response["sources_used"],
            latency_ms=llm_response["latency_ms"],
            model=llm_response["model"],
            escalation_required=escalation_required,
            escalation_reason=escalation_reason,
            retrieval_scores=retrieval_scores,
        )

    def ingest(self, docs_dir_override: Optional[str] = None) -> dict:
        """
        Full ingestion pipeline: load → chunk → embed → store.
        Returns ingestion statistics.
        """
        from pathlib import Path
        from src.ingestion.document_loader import load_documents_from_directory
        from src.ingestion.chunker import chunk_document

        docs_dir = Path(docs_dir_override) if docs_dir_override else settings.docs_path
        documents = load_documents_from_directory(docs_dir)

        if not documents:
            return {"documents": 0, "chunks": 0, "error": "No documents loaded"}

        all_chunks = []
        for doc in documents:
            chunks = chunk_document(
                doc,
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
            )
            all_chunks.extend(chunks)

        logger.info(f"Embedding {len(all_chunks)} chunks...")
        texts = [c.content for c in all_chunks]
        embeddings = self.embedder.embed(texts, batch_size=32)

        self.vector_store.upsert_chunks(all_chunks, embeddings)

        stats = {
            "documents": len(documents),
            "chunks": len(all_chunks),
            "vector_store_total": self.vector_store.count(),
        }
        logger.info(f"Ingestion complete: {stats}")
        return stats


# Module-level singleton
_pipeline: Optional[RAGPipeline] = None


def get_rag_pipeline() -> RAGPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = RAGPipeline()
    return _pipeline
