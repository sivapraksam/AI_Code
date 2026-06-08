"""
Hierarchical chunking strategy for compliance documents.

Strategy:
  1. Split document into sections using heading patterns (===, ---, numbered headings).
  2. Within each section, apply recursive character-level splitting at chunk_size tokens.
  3. Each chunk retains section title and document metadata for citation.
"""

import re
import hashlib
from typing import List, Tuple
from loguru import logger

from src.domain.policy.models import PolicyDocument, DocumentChunk

# Section heading patterns for compliance documents
_SECTION_PATTERNS = [
    # Underline style: =====
    re.compile(r"={5,}\n(.+?)\n={5,}", re.MULTILINE),
    # Underline style: -----
    re.compile(r"-{5,}\n(.+?)\n-{5,}", re.MULTILINE),
    # Numbered heading: "3. TITLE" or "3.1 TITLE"
    re.compile(r"^(\d+(?:\.\d+)*\.\s+[A-Z][A-Z\s\(\)&/]+)$", re.MULTILINE),
]

# Separators for recursive splitting (ordered from coarse to fine)
_SEPARATORS = ["\n\n\n", "\n\n", "\n", ". ", " ", ""]


def _chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    """
    Recursively split text by separators until chunks are within chunk_size characters.
    This is a simplified version of LangChain's RecursiveCharacterTextSplitter logic.
    """
    if len(text) <= chunk_size:
        return [text.strip()] if text.strip() else []

    for sep in _SEPARATORS:
        if sep and sep in text:
            splits = text.split(sep)
            chunks: List[str] = []
            current = ""
            for split in splits:
                candidate = (current + sep + split) if current else split
                if len(candidate) <= chunk_size:
                    current = candidate
                else:
                    if current.strip():
                        chunks.append(current.strip())
                    # Handle overlap: carry over last overlap chars
                    overlap_start = max(0, len(current) - chunk_overlap)
                    current = current[overlap_start:] + sep + split if current else split
            if current.strip():
                chunks.append(current.strip())
            # Filter out tiny fragments
            return [c for c in chunks if len(c) > 50]

    # Fallback: hard split
    return [
        text[i: i + chunk_size].strip()
        for i in range(0, len(text), chunk_size - chunk_overlap)
        if text[i: i + chunk_size].strip()
    ]


def _extract_sections(content: str) -> List[Tuple[str, str]]:
    """
    Split document content into (section_title, section_text) pairs.
    Returns list of tuples; title "" means document preamble.
    """
    # Try to find section boundaries using the heading patterns
    positions: List[Tuple[int, str]] = []
    for pattern in _SECTION_PATTERNS:
        for m in pattern.finditer(content):
            title = m.group(1).strip() if m.lastindex and m.lastindex >= 1 else m.group(0).strip()
            positions.append((m.start(), title))

    if not positions:
        # No section headings found — treat whole doc as one section
        return [("", content)]

    # Sort by position
    positions.sort(key=lambda x: x[0])

    sections: List[Tuple[str, str]] = []
    # Preamble before first section
    preamble = content[: positions[0][0]].strip()
    if preamble:
        sections.append(("", preamble))

    for i, (start, title) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(content)
        # Skip the heading line itself — find next newline
        section_start = content.find("\n", start) + 1 if "\n" in content[start:end] else start
        section_text = content[section_start:end].strip()
        if section_text:
            sections.append((title, section_text))

    return sections


def _make_chunk_id(document_id: str, chunk_index: int) -> str:
    raw = f"{document_id}::{chunk_index}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def chunk_document(
    document: PolicyDocument,
    chunk_size: int = 512,
    chunk_overlap: int = 64,
) -> List[DocumentChunk]:
    """
    Hierarchically chunk a policy document.
    Returns list of DocumentChunk objects with section context preserved.
    """
    if not document.content:
        logger.warning(f"Document {document.document_id} has no content — skipping chunking.")
        return []

    sections = _extract_sections(document.content)
    all_chunks: List[DocumentChunk] = []
    chunk_index = 0

    for section_title, section_text in sections:
        raw_chunks = _chunk_text(section_text, chunk_size, chunk_overlap)
        for raw_chunk in raw_chunks:
            chunk = DocumentChunk(
                chunk_id=_make_chunk_id(document.document_id, chunk_index),
                document_id=document.document_id,
                content=raw_chunk,
                chunk_index=chunk_index,
                section_title=section_title,
                metadata={
                    **document.to_metadata_dict(),
                    "section_title": section_title,
                    "chunk_index": chunk_index,
                },
            )
            all_chunks.append(chunk)
            chunk_index += 1

    logger.debug(
        f"Chunked {document.document_id} into {len(all_chunks)} chunks "
        f"(avg size: {sum(len(c.content) for c in all_chunks) // max(1, len(all_chunks))} chars)"
    )
    return all_chunks
