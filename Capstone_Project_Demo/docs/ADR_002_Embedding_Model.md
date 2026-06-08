# ADR-002: Embedding Model Selection

**Status:** Accepted  
**Date:** 2025-06-06  
**Deciders:** Architecture Team, Infrastructure Team  

---

## Context

The embedding model converts policy text and queries into vector representations for similarity search. Requirements:

1. **Local execution** — no external API calls for embeddings (data sovereignty, no PII leakage, no latency dependency on third-party embedding API).
2. **High quality** — must produce semantically meaningful embeddings for compliance/legal domain text.
3. **CPU-runnable** — production environment may not have GPU; must run acceptably on CPU.
4. **Small enough** to load in a compliance officer workstation environment.
5. **Dimension** small enough to keep ChromaDB index size manageable.

---

## Decision

**Selected: `BAAI/bge-small-en-v1.5`**

| Property | Value |
|----------|-------|
| Provider | Beijing Academy of AI (BAAI) — open source |
| Parameters | 33.4M |
| Embedding dimension | 384 |
| Max sequence length | 512 tokens |
| MTEB benchmark rank | Top-tier small model (MTEB Avg: 62.17) |
| License | MIT |
| Library | `sentence-transformers` |
| CPU inference speed | ~100–200 sentences/second on modern CPU |

### Why BGE-small-en-v1.5:

1. **MTEB performance:** Outperforms `all-MiniLM-L6-v2` on retrieval tasks (+3–5% on NDCG@10) while being the same parameter count.
2. **Retrieval-optimized:** BGE models are explicitly trained for retrieval tasks using contrastive learning on diverse text pairs — ideal for policy Q&A.
3. **Instruction prefix:** Supports `"Represent this sentence: "` prefix for asymmetric retrieval (query vs. passage), which we apply to query embedding.
4. **No external dependency:** Runs entirely locally via `sentence-transformers`.
5. **Fast CPU inference:** 33M parameters allow real-time query embedding (< 100ms per query on CPU).
6. **384-dim vectors:** Small enough that ChromaDB HNSW index is memory-efficient for 10K–100K chunks.

---

## Alternatives Considered

| Model | Params | MTEB Score | Why Rejected |
|-------|--------|------------|-------------|
| `all-MiniLM-L6-v2` | 22M | ~58 | Lower retrieval quality than BGE-small; not retrieval-optimized |
| `BAAI/bge-base-en-v1.5` | 109M | ~64 | Better quality but 3x larger; CPU inference 3x slower; rejected for latency |
| `BAAI/bge-large-en-v1.5` | 335M | ~65 | Similar quality to base; too large for CPU; rejected |
| `text-embedding-3-small` (OpenAI) | API | — | External API call — PII risk, network dependency, cost |
| `voyage-law-2` (Voyage AI) | API | — | Legal-domain specialized but external API; cost and data privacy concerns |
| `nomic-embed-text-v1` | 137M | ~62 | Good quality but 4x larger than BGE-small for marginal gain |
| `intfloat/e5-small-v2` | 33M | ~59 | Similar size to BGE-small but lower MTEB retrieval score |

---

## Implementation Details

- **Batch size:** 32 for ingestion (balance throughput vs. memory); 1 for query-time (single query).
- **Normalization:** L2-normalized embeddings (`normalize_embeddings=True`); enables cosine similarity via dot product.
- **Instruction prefix for BGE:** `"Represent this sentence: "` prepended to both documents and queries during ingestion and retrieval.
- **ChromaDB metric:** `cosine` (configured at collection creation).

---

## Consequences

**Positive:**
- Zero external API dependency for embeddings — PII stays local.
- Fast enough for real-time query (< 100ms embedding).
- High enough quality that reranker can select from meaningful candidates.

**Negative / Risks:**
- No domain-specific fine-tuning on banking/compliance text; mitigated by reranking step.
- 384-dim vectors provide less representational capacity than 1536-dim OpenAI embeddings; mitigated by high reranker quality.
- Model must be downloaded (~120MB) on first run; offline installation requires model caching.

---

## Future Consideration

If recall drops below 0.85 after adding more documents, evaluate fine-tuning BGE-small on bank-specific Q&A pairs using the RAGAS-generated training signal.
