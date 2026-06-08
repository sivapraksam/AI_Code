"""Domain models for the Regulation bounded context."""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional, List


class RegulatoryAuthority(str, Enum):
    OCC = "OCC"
    FDIC = "FDIC"
    FEDERAL_RESERVE = "Federal Reserve"
    CFPB = "CFPB"
    FINCEN = "FinCEN"
    SEC = "SEC"
    FATF = "FATF"
    BASEL_COMMITTEE = "Basel Committee"
    INTERNAL = "Internal"


class JurisdictionScope(str, Enum):
    FEDERAL = "federal"
    STATE = "state"
    INTERNATIONAL = "international"
    GLOBAL_STANDARD = "global_standard"


@dataclass
class RegulatoryRequirement:
    """A specific regulatory requirement extracted from a bulletin or guidance."""
    requirement_id: str
    regulation_name: str
    issuing_authority: RegulatoryAuthority
    jurisdiction: JurisdictionScope
    description: str
    effective_date: Optional[date]
    compliance_deadline: Optional[date]
    applicable_policy_ids: List[str] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)

    def to_metadata_dict(self) -> dict:
        return {
            "requirement_id": self.requirement_id,
            "regulation_name": self.regulation_name,
            "issuing_authority": self.issuing_authority.value,
            "jurisdiction": self.jurisdiction.value,
            "effective_date": str(self.effective_date) if self.effective_date else None,
        }


@dataclass
class RegulatoryBulletin:
    """Represents a regulatory bulletin or guidance document."""
    bulletin_id: str
    title: str
    issuing_authority: RegulatoryAuthority
    issue_date: date
    effective_date: Optional[date]
    summary: str
    file_path: str
    requirements: List[RegulatoryRequirement] = field(default_factory=list)
