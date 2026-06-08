# Compliance Knowledge Agent
## Banking & Financial Services RAG Pipeline

A production-grade Retrieval-Augmented Generation (RAG) system enabling compliance officers to ask natural-language questions against a bank's policy corpus with **citation-grounded answers**, **confidence scoring**, and **documented escalation paths**.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                   COMPLIANCE KNOWLEDGE AGENT                    │
│                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌─────────────┐ │
│  │ Document │   │Hierarchi-│   │ BGE-small│   │  ChromaDB   │ │
│  │ Loader   │──▶│cal Chunk-│──▶│ Embedder │──▶│ Vector Store│ │
│  │(txt/pdf) │   │  ing     │   │(local HF)│   │  (HNSW)     │ │
│  └──────────┘   └──────────┘   └──────────┘   └──────┬──────┘ │
│                                                        │        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    QUERY TIME                            │  │
│  │                                                          │  │
│  │  Question ──▶ BGE Embed ──▶ Vector Search (top-10)      │  │
│  │                              ──▶ Cross-Encoder Rerank    │  │
│  │                                  (ms-marco-MiniLM-L-6)   │  │
│  │                                  ──▶ Gemini 1.5 Flash    │  │
│  │                                      (citation prompt)   │  │
│  │                                      ──▶ RAGResponse     │  │
│  │                                          + Escalation    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Trust Architecture: AI-Recommend / Human-Approve              │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| API Framework | FastAPI | Async, typed, auto-docs |
| LLM | Google Gemini 1.5 Flash | Cost-effective, 1M token context |
| Embeddings | `BAAI/bge-small-en-v1.5` | Local HF, retrieval-optimized, 384-dim |
| Vector DB | ChromaDB (persistent) | Zero-infrastructure, cosine similarity |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` | High precision, 22M params, CPU-runnable |
| Evaluation | RAGAS | Faithfulness, Context Recall, Precision |
| Domain Model | DDD (Policy / Audit / Regulation) | Bounded context separation |

---

## Project Structure

```
D:\Capstone_Project_Demo\
├── main.py                          # FastAPI application
├── config.py                        # Pydantic settings
├── requirements.txt
├── .env.example                     # Copy to .env and fill in API key
│
├── data/
│   ├── synthetic_docs/              # 20 sanitized policy documents
│   │   ├── POL-AML-001_*.txt        # Anti-Money Laundering Policy
│   │   ├── POL-KYC-002_*.txt        # KYC & CDD Policy
│   │   ├── POL-CRM-003_*.txt        # Credit Risk Framework
│   │   ├── POL-ORM-004_*.txt        # Operational Risk Policy
│   │   ├── POL-DPR-005_*.txt        # Data Privacy & GDPR
│   │   ├── POL-CYB-006_*.txt        # Cybersecurity Policy
│   │   ├── POL-LQD-007_*.txt        # Liquidity Risk Policy
│   │   ├── POL-TPM-008_*.txt        # Third-Party Risk Policy
│   │   ├── POL-FRD-009_*.txt        # Fraud Risk Policy
│   │   ├── POL-WBS-010_*.txt        # Whistleblower Policy
│   │   ├── POL-MKT-011_*.txt        # Market Conduct Policy
│   │   ├── POL-IRR-012_*.txt        # Interest Rate Risk Policy
│   │   ├── POL-CPR-013_*.txt        # Consumer Protection Policy
│   │   ├── POL-ENV-014_*.txt        # ESG & Climate Risk Policy
│   │   ├── POL-CMP-015_*.txt        # Compliance Risk Program
│   │   ├── POL-TRN-016_*.txt        # Training & Competency Policy
│   │   ├── POL-CON-018_*.txt        # Conduct Risk Policy
│   │   ├── POL-AML-020_*.txt        # Sanctions / OFAC Policy
│   │   ├── REG-BUL-001_*.txt        # Basel III Bulletin
│   │   ├── REG-BUL-002_*.txt        # Dodd-Frank Bulletin
│   │   ├── REG-BUL-003_*.txt        # CFPB 2025 Priorities
│   │   ├── REG-BUL-004_*.txt        # Basel IV / FRTB
│   │   ├── REG-BUL-005_*.txt        # OCC Model Risk
│   │   ├── REG-BUL-006_*.txt        # CTA Beneficial Ownership
│   │   ├── AUD-FND-001_*.txt        # Q1 2025 AML Audit Findings
│   │   ├── AUD-FND-002_*.txt        # Q2 2025 KYC Audit Findings
│   │   ├── AUD-FND-003_*.txt        # Q3 2025 Cybersecurity Findings
│   │   └── AUD-FND-004_*.txt        # Q4 2024 Credit Risk Findings
│   ├── golden_set/
│   │   └── golden_qa_pairs.json     # 10 Q&A pairs for RAGAS evaluation
│   └── chroma_db/                   # ChromaDB persistent storage (auto-created)
│
├── src/
│   ├── domain/
│   │   ├── policy/models.py         # PolicyDocument, DocumentChunk
│   │   ├── audit/models.py          # AuditFinding, AuditReport
│   │   └── regulation/models.py     # RegulatoryRequirement, RegulatoryBulletin
│   ├── ingestion/
│   │   ├── document_loader.py       # Load txt/pdf, extract metadata
│   │   ├── chunker.py               # Hierarchical chunking
│   │   └── embedder.py              # BGE-small embeddings
│   ├── retrieval/
│   │   ├── vector_store.py          # ChromaDB operations
│   │   └── reranker.py              # Cross-encoder reranking
│   ├── generation/
│   │   └── llm_client.py            # Gemini API client + citation prompt
│   ├── pipeline/
│   │   └── rag_pipeline.py          # Orchestrator + escalation logic
│   └── evaluation/
│       └── ragas_eval.py            # RAGAS evaluation pipeline
│
├── scripts/
│   ├── ingest_documents.py          # CLI: ingest documents
│   └── run_evaluation.py            # CLI: run RAGAS evaluation
│
└── docs/
    ├── ADR_001_Chunking_Strategy.md
    ├── ADR_002_Embedding_Model.md
    ├── ADR_003_Vector_Database.md
    ├── ADR_004_Reranker.md
    ├── Trust_Boundary_Canvas.md
    └── Failure_Mode_Register.md
```

---

## Quick Start

### 1. Prerequisites

```powershell
# Python 3.11+ required
python --version

# Clone or open in D:\Capstone_Project_Demo
cd D:\Capstone_Project_Demo
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

*First run downloads BGE-small (~120MB) and cross-encoder (~90MB) from HuggingFace.*

### 3. Configure Environment

```powershell
copy .env.example .env
# Edit .env and add your GEMINI_API_KEY
notepad .env
```

Get a Gemini API key at: https://aistudio.google.com/app/apikey

### 4. Ingest Documents

```powershell
python scripts/ingest_documents.py
```

Expected output:
```
Documents:  20
Chunks:     ~420
Embeddings: ~420 (dim=384)
DB total:   ~420
```

### 5. Start the API Server

```powershell
python main.py
```

API available at: http://localhost:8000  
Swagger UI: http://localhost:8000/docs

### 6. Ask a Compliance Question

```powershell
curl -X POST http://localhost:8000/api/v1/ask `
  -H "Content-Type: application/json" `
  -d '{"question": "What is the SAR filing deadline under the AML policy?"}'
```

### 7. Run RAGAS Evaluation

```powershell
python scripts/run_evaluation.py
```

---

## API Reference

### POST `/api/v1/ask`

Submit a compliance question.

**Request:**
```json
{
  "question": "What are the EDD requirements for high-risk customers?",
  "top_k": 10,
  "document_type_filter": null
}
```

**Response:**
```json
{
  "question": "What are the EDD requirements for high-risk customers?",
  "answer": "High-risk customers require... [Source: POL-KYC-002, Section: ENHANCED DUE DILIGENCE]",
  "confidence": "HIGH",
  "citations": ["Source: POL-KYC-002, Section: ENHANCED DUE DILIGENCE FOR HIGH-RISK CUSTOMERS"],
  "sources": [...],
  "escalation_required": false,
  "escalation_reason": "",
  "latency_ms": 1243,
  "model": "gemini-1.5-flash",
  "trust_notice": "AI-Recommend / Human-Approve: ..."
}
```

### POST `/api/v1/ingest`

Trigger document ingestion.

```json
{"docs_dir": null, "reset": false}
```

### GET `/api/v1/health`

Health check and system status.

---

## RAGAS Evaluation Results

Target: **Faithfulness ≥ 0.90, Context Recall ≥ 0.85**

| Metric | Target | Description |
|--------|--------|-------------|
| Faithfulness | ≥ 0.90 | Answer claims are grounded in retrieved context (no hallucination) |
| Context Recall | ≥ 0.85 | Retrieved chunks cover the ground-truth answer |
| Context Precision | ≥ 0.80 | Retrieved chunks are relevant (not noisy) |

Results are saved to `./data/evaluation_results.json` after running the evaluation script.

---

## Architecture Decision Records (ADRs)

| ADR | Decision | Rationale |
|-----|----------|-----------|
| [ADR-001](docs/ADR_001_Chunking_Strategy.md) | Hierarchical chunking (512 chars, 64 overlap) | Section-title preservation for precise citations |
| [ADR-002](docs/ADR_002_Embedding_Model.md) | `BAAI/bge-small-en-v1.5` | Best small model for retrieval; local HF; 384-dim |
| [ADR-003](docs/ADR_003_Vector_Database.md) | ChromaDB PersistentClient | Zero-infrastructure; cosine similarity; metadata filtering |
| [ADR-004](docs/ADR_004_Reranker.md) | `cross-encoder/ms-marco-MiniLM-L-6-v2` | High precision; MS MARCO retrieval training |

---

## Trust Architecture

Every answer is tagged **AI-Recommend / Human-Approve**. See [Trust Boundary Canvas](docs/Trust_Boundary_Canvas.md) for the full capability map.

Escalation is automatically triggered for:
- Low-confidence responses (reranker score < 0.50)
- Jurisdiction-specific queries (state law, EU/GDPR, etc.)
- Policy boundary questions (ambiguity between two policies)

---

## Failure Mode Register

See [Failure_Mode_Register.md](docs/Failure_Mode_Register.md) for 8 failure modes including:
- **Row 1 (CRITICAL):** Regulatory Misstatement — RPN 120
- **Row 3:** Outdated Policy Info — RPN 120
- **Row 4:** Out-of-Corpus Query — RPN 112

---

## Domain Model (DDD)

Three bounded contexts with clear interfaces:

| Context | Aggregate Root | Key Entities |
|---------|---------------|-------------|
| **Policy** | `PolicyDocument` | `DocumentChunk` |
| **Audit** | `AuditReport` | `AuditFinding` |
| **Regulation** | `RegulatoryBulletin` | `RegulatoryRequirement` |

---

## Compliance Disclaimer

This system is a **decision-support tool** for qualified compliance professionals. It does not constitute legal advice and must not be used as the sole basis for regulatory decisions. All AI-generated answers require human review before action. See the [Trust Boundary Canvas](docs/Trust_Boundary_Canvas.md) for the complete trust architecture.
