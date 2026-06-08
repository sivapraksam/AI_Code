"""Domain models for the Audit bounded context."""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional, List


class FindingSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingStatus(str, Enum):
    OPEN = "open"
    IN_REMEDIATION = "in_remediation"
    CLOSED = "closed"
    OVERDUE = "overdue"


@dataclass
class AuditFinding:
    """Represents an audit finding from an internal audit report."""
    finding_id: str
    audit_report_id: str
    title: str
    severity: FindingSeverity
    status: FindingStatus
    condition: str
    criteria: str
    cause: str
    effect: str
    management_response: str
    remediation_date: Optional[date]
    responsible_owner: str
    related_policy_ids: List[str] = field(default_factory=list)

    def to_metadata_dict(self) -> dict:
        return {
            "finding_id": self.finding_id,
            "audit_report_id": self.audit_report_id,
            "title": self.title,
            "severity": self.severity.value,
            "status": self.status.value,
            "remediation_date": str(self.remediation_date) if self.remediation_date else None,
            "responsible_owner": self.responsible_owner,
        }


@dataclass
class AuditReport:
    """Represents a complete internal audit report."""
    report_id: str
    title: str
    audit_period_start: date
    audit_period_end: date
    report_date: date
    overall_rating: str
    findings: List[AuditFinding] = field(default_factory=list)
    file_path: str = ""
