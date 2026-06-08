# ADR-003: Vector Database Selection

**Status:** Accepted  
**Date:** 2025-06-06  
**Deciders:** Architecture Team, Infrastructure Team  

---

## Context

The vector database stores embeddings and metadata for all document chunks, enabling fast approximate nearest-neighbor (ANN) search at query time. Requirements:

1. **Local / embedded** — runs in-process or on a single machine; no separate server to manage.
2. **Persistent** — data survives process restarts.
3. **Metadata filtering** — filter by `document_type` (policy/regulatory_bulletin/audit_finding).
4. **Cosine similarity** — required for BGE embeddings.
5. **Python-native** — seamless integration without JVM or C++ toolchain requirements.
6. **Scales to ~50K–500K chunks** — corpus could grow from 20 to 5,000 documents.

---

## Decision

**Selected: ChromaDB (PersistentClient mode)**

| Property | Value |
|----------|-------|
| Architecture | Embedded (in-process) with SQLite + HNSW index |
| Persistence | SQLite on disk (`./data/chroma_db/`) |
| ANN Algorithm | HNSW (hnswlib) |
| Distance metrics | cosine, l2, ip |
| Metadata filtering | Yes (WHERE clauses on metadata fields) |
| Max scale (embedded) | ~1M vectors |
| Python library | `chromadb` |
| License | Apache 2.0 |

### Why ChromaDB:

1. **Zero-infrastructure:** PersistentClient runs in-process; no Docker, no server, no network — ideal for single-machine deployment and compliance analyst workstations.
2. **Metadata filtering:** Native support for `where={"document_type": "policy"}` filtering without additional logic.
3. **HNSW index:** Near-O(log n) search; handles 100K+ chunks with < 50ms latency.
4. **Cosine metric:** Configured at collection creation — compatible with normalized BGE embeddings.
5. **Batch upsert:** Efficient bulk ingestion with automatic deduplication via chunk ID.
6. **Active community:** Most actively maintained embedded vector DB for Python as of 2025.

---

## Alternatives Considered

| Database | Why Rejected |
|----------|-------------|
| **FAISS** (Meta) | Excellent performance but requires manual persistence code; no built-in metadata filtering; would need separate SQLite for metadata joins |
| **Qdrant** (local mode) | Very capable but requires Rust binary / Docker for server mode; heavier operational footprint |
| **Pinecone** | Managed cloud service — data sovereignty concerns for compliance documents containing PII indicators; ongoing cost |
| **Weaviate** | Requires Docker/Kubernetes; too heavy for single-machine compliance workstation deployment |
| **pgvector (PostgreSQL)** | Excellent if PostgreSQL already deployed; adds infrastructure dependency not warranted for initial deployment |
| **LanceDB** | Promising embedded DB but less mature than ChromaDB as of 2025; fewer production references |
| **Milvus Lite** | Embedded mode available but Milvus is primarily designed for large-scale deployments; heavier than needed |

---

## Architecture Details

```
Collection: compliance_docs
  Metric: cosine
  
Chunk document → {
  id:        MD5(document_id + "::" + chunk_index)[:12]
  embedding: [384-dim float array]
  document:  chunk.content (text)
  metadata: {
    document_id:    string
    title:          string
    document_type:  "policy" | "regulatory_bulletin" | "audit_finding"
    version:        string
    effective_date: string
    owner:          string
    section_title:  string
    chunk_index:    string
    citation:       "Source: DOC-ID, Section: TITLE"
  }
}
```

**Index Configuration:** Default HNSW parameters (`M=16`, `ef_construction=100`); adequate for corpus size.

---

## Consequences

**Positive:**
- Single `pip install chromadb` — no infrastructure provisioning.
- SQLite persistence is reliable and survives restarts.
- Metadata filtering enables document-type-scoped queries.

**Negative / Risks:**
- Single-process: concurrent write access from multiple processes unsupported; mitigated by single-instance API design.
- Not suitable for distributed deployment without migration to ChromaDB server mode or Qdrant.
- HNSW index is approximate; a small number of relevant chunks may be missed — mitigated by reranking.

---

## Migration Path

If corpus exceeds 500K chunks or multi-instance deployment is required, migrate to:
1. **ChromaDB HTTP server mode** (same client API, add server process) — zero code changes.
2. **Qdrant** (same HNSW algorithm, REST API available) — adapter change in `vector_store.py` only.
