"""
Google Gemini API client for compliance answer generation.
Implements citation-required prompting and confidence scoring.
Trust Architecture: All answers are AI-Recommend / Human-Approve.

Uses the google-genai SDK (replaces deprecated google-generativeai).
"""

import time
from typing import List, Optional
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import settings

# System prompt enforcing citation-grounded, compliance-safe responses
SYSTEM_PROMPT = """You are a compliance knowledge assistant for a regional bank.
Your role is to help compliance officers find accurate information from the bank's policy corpus.

CRITICAL RULES:
1. Answer ONLY from the provided context. Do not use any external knowledge.
2. Every factual claim MUST be followed by a citation in the format: [Source: DOCUMENT_ID, Section: SECTION_TITLE]
3. If the context does not contain sufficient information to answer the question, respond with:
   "INSUFFICIENT_CONTEXT: The provided documents do not contain enough information to answer this question. Please consult the Compliance team or relevant subject matter expert."
4. If the question spans multiple policy areas or jurisdictions, explicitly note the scope of your answer.
5. Never speculate, infer, or extrapolate beyond what is explicitly stated in the context.
6. Confidence Level: End every response with "Confidence: HIGH | MEDIUM | LOW" based on how completely the context addresses the question.

TRUST NOTICE: This response is AI-generated and must be reviewed by a qualified compliance officer before any action is taken. This tool provides AI-Recommend guidance; Human-Approve is required.
"""

ANSWER_PROMPT_TEMPLATE = """CONTEXT (retrieved policy documents):
{context}

QUESTION: {question}

Provide a precise, citation-grounded answer following all rules above.
Include at least one citation per substantive claim.
"""

CONFIDENCE_THRESHOLDS = {
    "HIGH": 0.75,
    "MEDIUM": 0.50,
    "LOW": 0.0,
}


class GeminiLLMClient:
    """Google Gemini API client with retry logic and citation enforcement."""

    def __init__(self):
        self._model = None

    def _init_model(self):
        if self._model is None:
            if not settings.gemini_api_key:
                raise ValueError(
                    "GEMINI_API_KEY is not set. Please add it to your .env file."
                )
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            self._model = genai.GenerativeModel(
                model_name=settings.gemini_model,
                system_instruction=SYSTEM_PROMPT,
                generation_config={
                    "temperature": settings.gemini_temperature,
                    "max_output_tokens": settings.gemini_max_tokens,
                    "candidate_count": 1,
                },
            )
            logger.info(f"Gemini model '{settings.gemini_model}' initialised.")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def generate_answer(
        self,
        question: str,
        context_chunks: List[dict],
        top_rerank_score: float = 0.0,
    ) -> dict:
        """
        Generate a citation-grounded compliance answer.

        Args:
            question: The compliance officer's question.
            context_chunks: Reranked and retrieved document chunks.
            top_rerank_score: Highest reranker score (for confidence estimation).

        Returns:
            dict with keys: answer, citations, confidence, sources_used, latency_ms.
        """
        self._init_model()
        start_time = time.perf_counter()

        # Build context block with citations
        context_parts = []
        citations_used = []
        for i, chunk in enumerate(context_chunks, 1):
            meta = chunk.get("metadata", {})
            doc_id = meta.get("document_id", "UNKNOWN")
            section = meta.get("section_title", "")
            citation = meta.get("citation", f"Source: {doc_id}")
            context_parts.append(
                f"[{i}] {citation}\n{chunk['content']}"
            )
            citations_used.append(citation)

        context_text = "\n\n---\n\n".join(context_parts)
        prompt = ANSWER_PROMPT_TEMPLATE.format(
            context=context_text,
            question=question,
        )

        response = self._model.generate_content(prompt)
        answer_text = response.text.strip() if response.text else "No response generated."

        latency_ms = int((time.perf_counter() - start_time) * 1000)
        confidence = self._estimate_confidence(answer_text, top_rerank_score)

        return {
            "answer": answer_text,
            "citations": citations_used,
            "confidence": confidence,
            "sources_used": len(context_chunks),
            "latency_ms": latency_ms,
            "model": settings.gemini_model,
        }

    def _estimate_confidence(self, answer_text: str, top_rerank_score: float) -> str:
        """Estimate confidence level based on answer content and retrieval scores."""
        if "INSUFFICIENT_CONTEXT" in answer_text:
            return "LOW"
        if top_rerank_score >= CONFIDENCE_THRESHOLDS["HIGH"]:
            return "HIGH"
        if top_rerank_score >= CONFIDENCE_THRESHOLDS["MEDIUM"]:
            return "MEDIUM"
        return "LOW"

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Estimate cost in USD for Gemini 1.5 Flash.
        Pricing as of 2025: $0.075 per 1M input tokens, $0.30 per 1M output tokens.
        """
        input_cost = (prompt_tokens / 1_000_000) * 0.075
        output_cost = (completion_tokens / 1_000_000) * 0.30
        return round(input_cost + output_cost, 6)


# Module-level singleton
_llm_client: Optional[GeminiLLMClient] = None


def get_llm_client() -> GeminiLLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = GeminiLLMClient()
    return _llm_client
