"""Domain models for the Policy bounded context."""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class DocumentType(str, Enum):
    POLICY = "policy"
    REGULATORY_BULLETIN = "regulatory_bulletin"
    AUDIT_FINDING = "audit_finding"
    PROCEDURE = "procedure"
    GUIDANCE = "guidance"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PolicyDocument:
    """Represents a compliance policy document in the Policy bounded context."""
    document_id: str
    title: str
    document_type: DocumentType
    version: str
    effective_date: Optional[date]
    owner: str
    file_path: str
    classification: str = "Internal — Restricted"
    content: str = ""
    metadata: dict = field(default_factory=dict)

    def to_metadata_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "title": self.title,
            "document_type": self.document_type.value,
            "version": self.version,
            "effective_date": str(self.effective_date) if self.effective_date else None,
            "owner": self.owner,
            "file_path": self.file_path,
            "classification": self.classification,
        }


@dataclass
class DocumentChunk:
    """A semantically meaningful chunk of a policy document."""
    chunk_id: str
    document_id: str
    content: str
    chunk_index: int
    section_title: str = ""
    page_number: Optional[int] = None
    metadata: dict = field(default_factory=dict)

    @property
    def citation(self) -> str:
        """Produces a human-readable citation string."""
        parts = [f"Source: {self.document_id}"]
        if self.section_title:
            parts.append(f"Section: {self.section_title}")
        return ", ".join(parts)
