"""
Document loader for the ingestion pipeline.
Loads .txt and .pdf files from the synthetic_docs directory,
extracts metadata from document headers, and maps to domain models.
"""

import re
from pathlib import Path
from typing import List, Optional
from loguru import logger

from src.domain.policy.models import PolicyDocument, DocumentType


# Regex patterns for extracting metadata from document headers
_PATTERNS = {
    "document_id": re.compile(r"DOCUMENT ID:\s*(.+)", re.IGNORECASE),
    "title": re.compile(r"TITLE:\s*(.+)", re.IGNORECASE),
    "version": re.compile(r"VERSION:\s*(.+)", re.IGNORECASE),
    "owner": re.compile(r"OWNER:\s*(.+)", re.IGNORECASE),
    "classification": re.compile(r"CLASSIFICATION:\s*(.+)", re.IGNORECASE),
}

_DOC_TYPE_MAP = {
    "POL": DocumentType.POLICY,
    "REG": DocumentType.REGULATORY_BULLETIN,
    "AUD": DocumentType.AUDIT_FINDING,
}


def _infer_document_type(document_id: str, filename: str) -> DocumentType:
    """Infer document type from document ID prefix or filename."""
    prefix = document_id.split("-")[0].upper() if document_id else ""
    if prefix in _DOC_TYPE_MAP:
        return _DOC_TYPE_MAP[prefix]
    filename_lower = filename.lower()
    if "audit" in filename_lower or "finding" in filename_lower:
        return DocumentType.AUDIT_FINDING
    if "bulletin" in filename_lower or "regulatory" in filename_lower:
        return DocumentType.REGULATORY_BULLETIN
    return DocumentType.POLICY


def _extract_metadata(content: str) -> dict:
    """Extract structured metadata from the first 20 lines of a document."""
    header_block = "\n".join(content.splitlines()[:20])
    result = {}
    for field, pattern in _PATTERNS.items():
        match = pattern.search(header_block)
        result[field] = match.group(1).strip() if match else ""
    return result


def load_document(file_path: Path) -> Optional[PolicyDocument]:
    """Load a single document file and return a PolicyDocument."""
    try:
        suffix = file_path.suffix.lower()
        if suffix == ".txt":
            content = file_path.read_text(encoding="utf-8", errors="replace")
        elif suffix == ".pdf":
            content = _load_pdf(file_path)
        else:
            logger.warning(f"Unsupported file type: {file_path.suffix} — skipping {file_path.name}")
            return None

        meta = _extract_metadata(content)
        doc_id = meta.get("document_id") or file_path.stem
        doc_type = _infer_document_type(doc_id, file_path.name)

        return PolicyDocument(
            document_id=doc_id,
            title=meta.get("title") or file_path.stem.replace("_", " "),
            document_type=doc_type,
            version=meta.get("version") or "1.0",
            effective_date=None,
            owner=meta.get("owner") or "Unknown",
            file_path=str(file_path),
            classification=meta.get("classification") or "Internal",
            content=content,
            metadata={"filename": file_path.name, "file_size_bytes": file_path.stat().st_size},
        )
    except Exception as exc:
        logger.error(f"Failed to load document {file_path}: {exc}")
        return None


def _load_pdf(file_path: Path) -> str:
    """Extract text from a PDF file using pypdf."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(file_path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)
    except ImportError:
        logger.warning("pypdf not installed; cannot load PDF files.")
        return ""


def load_documents_from_directory(docs_dir: Path) -> List[PolicyDocument]:
    """Load all supported documents from a directory."""
    documents: List[PolicyDocument] = []
    supported_extensions = {".txt", ".pdf"}

    if not docs_dir.exists():
        logger.error(f"Documents directory does not exist: {docs_dir}")
        return documents

    files = [
        f for f in docs_dir.iterdir()
        if f.is_file() and f.suffix.lower() in supported_extensions
    ]
    logger.info(f"Found {len(files)} document(s) in {docs_dir}")

    for file_path in sorted(files):
        doc = load_document(file_path)
        if doc:
            documents.append(doc)
            logger.debug(f"Loaded: {doc.document_id} — {doc.title}")

    logger.info(f"Successfully loaded {len(documents)} document(s)")
    return documents
