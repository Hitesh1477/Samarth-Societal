"""
Duplicate detection schemas.

Matches frontend interfaces in frontend/src/types/index.ts:
- DuplicateReport
- DuplicateCluster
"""

from typing import Optional
from pydantic import Field
from app.schemas.base import CamelModel


class DuplicateReportSchema(CamelModel):
    """
    Matches frontend `DuplicateReport` interface exactly.

    camelCase aliases (via CamelModel):
        reportId, title, similarity, distance, date, location, reporter
    """
    report_id: str
    title: str
    similarity: float = Field(ge=0.0, le=1.0)
    distance: str
    date: str
    location: str
    reporter: str


class DuplicateClusterSchema(CamelModel):
    """
    Matches frontend `DuplicateCluster` interface exactly.

    camelCase aliases (via CamelModel):
        problemId, totalReports, similarity, reports, unifiedChallengeId
    """
    problem_id: str
    total_reports: int = Field(ge=1)
    similarity: float = Field(ge=0.0, le=1.0)
    reports: list[DuplicateReportSchema] = Field(default_factory=list)
    unified_challenge_id: Optional[str] = None
