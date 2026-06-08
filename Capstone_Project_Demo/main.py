"""
FastAPI application for the Compliance Knowledge Agent.
Endpoints:
  POST /api/v1/ask       — Submit a compliance question
  POST /api/v1/ingest    — Trigger document ingestion
  GET  /api/v1/health    — Health check
  POST /api/v1/evaluate  — Run RAGAS evaluation on golden set
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from loguru import logger
import uvicorn

from config import settings

app = FastAPI(
    title="Compliance Knowledge Agent",
    description=(
        "RAG-powered compliance Q&A for banking policy documents. "
        "All answers are AI-Recommend / Human-Approve."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# Request / Response models
# ─────────────────────────────────────────────

class AskRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=2000, description="Compliance question")
    top_k: Optional[int] = Field(default=None, ge=1, le=20, description="Number of chunks to retrieve")
    document_type_filter: Optional[str] = Field(default=None, description="Filter by document type")


class CitedSource(BaseModel):
    citation: str
    content_preview: str
    rerank_score: float


class AskResponse(BaseModel):
    question: str
    answer: str
    confidence: str
    citations: List[str]
    sources: List[CitedSource]
    escalation_required: bool
    escalation_reason: str
    latency_ms: int
    model: str
    trust_notice: str = (
        "AI-Recommend / Human-Approve: This response must be reviewed by a "
        "qualified compliance officer before any action is taken."
    )


class IngestRequest(BaseModel):
    docs_dir: Optional[str] = Field(default=None, description="Override docs directory path")
    reset: bool = Field(default=False, description="Delete existing collection before ingesting")


class IngestResponse(BaseModel):
    status: str
    documents_loaded: int
    chunks_created: int
    vector_store_total: int


class HealthResponse(BaseModel):
    status: str
    vector_store_count: int
    embedding_model: str
    llm_model: str


# ─────────────────────────────────────────────
# Startup event — lazy pipeline init
# ─────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    logger.info("Compliance Knowledge Agent starting up...")
    logger.info(f"Embedding model: {settings.embedding_model}")
    logger.info(f"LLM model: {settings.gemini_model}")
    logger.info(f"Vector store: {settings.chroma_persist_dir}")


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@app.get("/api/v1/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check — returns model configuration and vector store status."""
    try:
        from src.retrieval.vector_store import get_vector_store
        vs = get_vector_store()
        count = vs.count()
    except Exception:
        count = -1

    return HealthResponse(
        status="ok",
        vector_store_count=count,
        embedding_model=settings.embedding_model,
        llm_model=settings.gemini_model,
    )


@app.post("/api/v1/ingest", response_model=IngestResponse, tags=["Ingestion"])
async def ingest_documents(request: IngestRequest):
    """
    Trigger document ingestion from the configured docs directory.
    Loads, chunks, embeds, and stores all documents in ChromaDB.
    """
    try:
        from src.pipeline.rag_pipeline import get_rag_pipeline
        from src.retrieval.vector_store import get_vector_store

        pipeline = get_rag_pipeline()

        if request.reset:
            logger.warning("Reset requested — deleting existing vector store collection.")
            get_vector_store().delete_collection()

        stats = pipeline.ingest(docs_dir_override=request.docs_dir)

        return IngestResponse(
            status="success",
            documents_loaded=stats.get("documents", 0),
            chunks_created=stats.get("chunks", 0),
            vector_store_total=stats.get("vector_store_total", 0),
        )
    except Exception as exc:
        logger.exception(f"Ingestion failed: {exc}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(exc)}")


@app.post("/api/v1/ask", response_model=AskResponse, tags=["Query"])
async def ask_question(request: AskRequest):
    """
    Submit a natural-language compliance question.
    Returns a citation-grounded answer with confidence and escalation metadata.

    Trust Architecture: All answers are AI-Recommend / Human-Approve.
    Low-confidence answers and jurisdiction-specific queries trigger escalation flags.
    """
    try:
        from src.pipeline.rag_pipeline import get_rag_pipeline
        pipeline = get_rag_pipeline()

        response = pipeline.query(
            question=request.question,
            top_k_retrieval=request.top_k,
            document_type_filter=request.document_type_filter,
        )

        sources = [
            CitedSource(
                citation=chunk.get("metadata", {}).get("citation", ""),
                content_preview=chunk["content"][:300] + "..." if len(chunk["content"]) > 300 else chunk["content"],
                rerank_score=round(chunk.get("rerank_score", 0.0), 4),
            )
            for chunk in response.retrieved_chunks
        ]

        return AskResponse(
            question=response.question,
            answer=response.answer,
            confidence=response.confidence,
            citations=response.citations,
            sources=sources,
            escalation_required=response.escalation_required,
            escalation_reason=response.escalation_reason,
            latency_ms=response.latency_ms,
            model=response.model,
        )

    except ValueError as exc:
        # Missing API key or config error
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.exception(f"Query failed: {exc}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(exc)}")


@app.post("/api/v1/evaluate", tags=["Evaluation"])
async def run_evaluation(background_tasks: BackgroundTasks):
    """
    Trigger RAGAS evaluation on the golden Q&A set.
    Runs in background; check logs for results.
    """
    background_tasks.add_task(_run_ragas_evaluation)
    return {"status": "evaluation_started", "message": "Check logs for RAGAS scorecard results."}


async def _run_ragas_evaluation():
    """Background task for RAGAS evaluation."""
    try:
        from src.evaluation.ragas_eval import run_ragas_evaluation
        results = run_ragas_evaluation()
        logger.info(f"RAGAS Evaluation Results: {results}")
    except Exception as exc:
        logger.exception(f"RAGAS evaluation failed: {exc}")


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
        log_level=settings.log_level.lower(),
    )
