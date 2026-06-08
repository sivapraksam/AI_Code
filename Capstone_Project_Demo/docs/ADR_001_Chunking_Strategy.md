# ADR-001: Chunking Strategy

**Status:** Accepted  
**Date:** 2025-06-06  
**Deciders:** Architecture Team, Compliance SME  

---

## Context

The corpus consists of 20 compliance documents (policies, regulatory bulletins, audit findings) with a range of ~500 to ~3,000 words each. Documents have well-defined section headings using either `===` underlines or numbered sections (e.g., `3.1 TITLE`). 

Compliance officers ask both narrow factual questions (e.g., "What is the SAR filing deadline?") and broader thematic questions (e.g., "What are all the escalation procedures across our policies?"). The chunking strategy must:

1. Preserve regulatory precision — a misquoted threshold is a regulatory risk.
2. Retain enough context for Gemini to generate accurate, citation-grounded answers.
3. Keep chunk sizes manageable for the cross-encoder reranker (max 512 tokens).
4. Enable accurate citation back to document section (not just document name).

---

## Decision

**Hierarchical Chunking with Section-Aware Splitting**

### Algorithm:

1. **Level 1 — Section Extraction:** Parse document content for structural headings using regex patterns for `=====` underlines and `N.N TITLE` patterns. This creates one text block per section.

2. **Level 2 — Recursive Character Splitting:** Within each section, apply a recursive splitter with:
   - `chunk_size = 512 characters` (≈ 128–140 tokens, well within reranker limits)
   - `chunk_overlap = 64 characters` (≈ 12% overlap — enough to preserve cross-sentence context without significant redundancy)
   - Separator hierarchy: `\n\n\n → \n\n → \n → . → (space)`

3. **Section Title Preservation:** Each chunk retains `section_title` in its metadata, enabling the citation format `[Source: DOC-ID, Section: SECTION-TITLE]`.

4. **Minimum Chunk Length:** Chunks shorter than 50 characters are discarded (typically empty section headings or whitespace).

### Parameters:

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| chunk_size | 512 chars | Fits cross-encoder (512 token max) with buffer; preserves full sentences |
| chunk_overlap | 64 chars | 12.5% — captures sentence context across chunk boundary |
| Section extraction | Regex-based | Compliance docs have consistent heading format |
| Min chunk length | 50 chars | Eliminates header-only fragments |

---

## Alternatives Considered

| Option | Why Rejected |
|--------|-------------|
| **Fixed-size sliding window** (no section awareness) | Loses section context; citations cannot point to a specific policy section — regulatory risk |
| **Sentence-level chunking** | Creates very small chunks (1–3 sentences) that lose regulatory context; increases retrieval noise |
| **Document-level chunking** | Chunks too large for reranker; dilutes relevance signal; Gemini context window filled with irrelevant text |
| **Semantic chunking** (embedding-similarity based splits) | Requires additional compute; adds complexity without clear benefit for well-structured regulatory text |
| **LangChain RecursiveCharacterTextSplitter** | Functionally equivalent to our implementation; chose custom implementation to control section-title metadata injection |

---

## Consequences

**Positive:**
- Section title preserved in every chunk enables precise citations (e.g., `[Source: POL-AML-001, Section: SUSPICIOUS ACTIVITY REPORTING]`).
- Chunk sizes are predictable and reranker-friendly.
- Hierarchical approach is extensible — can add paragraph-level splitting for future very large documents.

**Negative / Risks:**
- Section regex patterns must be updated if document format changes (e.g., new heading style adopted).
- Overlap creates minor redundancy in the vector index; acceptable given 20-document corpus size.
- Very short sections (< 100 chars) may produce single very-small chunks; mitigated by 50-char minimum.

---

## Monitoring

- Log average chunk size per document at ingestion time.
- Alert if any document produces > 200 chunks (suggests very large or malformed document).
- Review context recall metric from RAGAS; if < 0.85, consider increasing chunk_overlap.
