# ADR-004: Reranker Selection

**Status:** Accepted  
**Date:** 2025-06-06  
**Deciders:** Architecture Team  

---

## Context

The RAG pipeline uses a two-stage retrieval approach:
1. **Stage 1 (Recall):** Bi-encoder embedding search (fast, approximate) → top 10 candidates.
2. **Stage 2 (Precision):** Reranker (cross-encoder) → top 5 most relevant chunks.

The reranker is critical for compliance use cases because:
- A bi-encoder may return semantically similar but legally distinct chunks (e.g., two different threshold values).
- The cross-encoder scores (query, passage) pairs directly, capturing nuanced query-passage interaction.
- Wrong regulatory thresholds in answers carry real regulatory risk; precision matters more than speed at this stage.

Requirements:
1. **High precision** on compliance/legal Q&A pairs.
2. **Fast enough** for real-time use: target < 500ms for 10 candidates.
3. **Local execution** — no API dependency.
4. **Max 512 tokens** per passage (aligned with chunk size).

---

## Decision

**Selected: `cross-encoder/ms-marco-MiniLM-L-6-v2`**

| Property | Value |
|----------|-------|
| Architecture | BERT-based cross-encoder |
| Parameters | ~22M |
| Training data | MS MARCO passage ranking dataset (500K+ query-passage pairs) |
| Input | [CLS] query [SEP] passage [SEP] |
| Output | Single relevance score (higher = more relevant) |
| Max tokens | 512 |
| Inference latency | ~50–200ms for 10 candidates on CPU |
| Library | `sentence-transformers` (CrossEncoder class) |
| License | Apache 2.0 |

### Why ms-marco-MiniLM-L-6-v2:

1. **MS MARCO training:** Trained on real information retrieval query-passage pairs, not just semantic similarity — directly applicable to Q&A retrieval.
2. **Size vs. quality tradeoff:** At 22M parameters, provides strong reranking quality within acceptable CPU latency.
3. **Established baseline:** Most referenced reranker in production RAG systems; well-characterized performance.
4. **512-token limit:** Aligned with our 512-character chunk size (~128 tokens), so no truncation occurs.
5. **Same library:** Uses `sentence-transformers.CrossEncoder`, already installed for the embedding model.

---

## Alternatives Considered

| Model | Why Considered | Why Rejected |
|-------|---------------|-------------|
| `cross-encoder/ms-marco-MiniLM-L-12-v2` | Better quality (L-12 vs L-6) | 2x slower on CPU; marginal quality gain over L-6 for our domain |
| `BAAI/bge-reranker-base` | BGE reranker, good domain generalization | Requires separate download; L-6 MiniLM sufficient for current corpus |
| `BAAI/bge-reranker-large` | Best quality BGE reranker | 400ms+ per query on CPU — too slow for real-time compliance use |
| `Cohere Rerank API` | Excellent quality, legal-domain fine-tuned available | External API — PII risk, network dependency, cost, availability risk |
| `Jina Reranker v2` | Strong performance | External API dependency; local model requires more RAM than L-6 |
| No reranker (bi-encoder only) | Simpler architecture | Insufficient precision for regulatory Q&A; risk of wrong thresholds in answers |

---

## Reranking Configuration

```python
# Stage 1: Vector search — top 10 candidates (high recall)
candidates = vector_store.similarity_search(query_embedding, top_k=10)

# Stage 2: Cross-encoder reranking — top 5 (high precision)
pairs = [(query, candidate["content"]) for candidate in candidates]
scores = cross_encoder.predict(pairs)
reranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)[:5]
```

**Confidence Estimation:**
- Top reranker score ≥ 0.75 → HIGH confidence
- Top reranker score ≥ 0.50 → MEDIUM confidence  
- Top reranker score < 0.50 → LOW confidence → triggers escalation flag

---

## Consequences

**Positive:**
- Significantly improves precision over bi-encoder alone on regulatory Q&A.
- Catches cases where two chunks use similar language but refer to different policies.
- Confidence score from reranker provides a calibrated signal for escalation decisions.

**Negative / Risks:**
- Adds ~100–300ms latency per query on CPU (acceptable for compliance officer use case; not real-time trading).
- Cross-encoder not fine-tuned on banking compliance domain; performance on very domain-specific terminology may be suboptimal.
- If corpus grows to 10K+ documents, retrieval top-k may need to increase, adding reranking latency.

---

## Monitoring

- Log reranker latency per query; alert if P95 > 1s.
- Log distribution of top reranker scores; investigate if most queries have low scores (< 0.3) — suggests retrieval or chunking problem.
- Measure RAGAS faithfulness and context precision monthly; if precision drops, consider upgrading to BGE-reranker-large.
