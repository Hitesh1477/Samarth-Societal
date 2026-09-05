"""
Problem domain schemas.

All fields are snake_case internally; CamelModel serialises them to camelCase
on the wire to match the frontend TypeScript types exactly.

Frontend reference: frontend/src/types/index.ts
"""

from typing import Optional
from pydantic import Field, field_validator

from app.schemas.base import CamelModel
from app.schemas.enums import (
    EvidenceType,
    ProblemCategory,
    ProblemStatus,
    UrgencyLevel,
)


# ── Location ──────────────────────────────────────────────────────────────────

class LocationSchema(CamelModel):
    """Matches frontend `ProblemReport.location`."""
    lat: float
    lng: float
    name: str
    district: str


# ── Evidence ──────────────────────────────────────────────────────────────────

class EvidenceSchema(CamelModel):
    """Matches frontend `Evidence` type."""
    id: str
    type: EvidenceType
    url: str
    name: str


# ── ProblemReport (API Response) ──────────────────────────────────────────────

class ProblemReportSchema(CamelModel):
    """
    Matches frontend `ProblemReport` exactly.

    camelCase aliases (via CamelModel):
        affectedPopulation, createdAt, reporterName, challengeId
    """
    id: str
    title: str
    description: str
    category: ProblemCategory
    subcategory: str
    urgency: UrgencyLevel
    affected_population: int = Field(ge=0)      # → affectedPopulation
    location: LocationSchema
    evidence: list[EvidenceSchema] = []
    status: ProblemStatus
    challenge_id: Optional[str] = None          # → challengeId
    similarity: Optional[float] = None
    distance: Optional[str] = None
    created_at: str                             # → createdAt  (ISO-8601 string)
    reporter_name: str                          # → reporterName


# ── SubmitProblemData (Request Body) ─────────────────────────────────────────

class SubmitProblemRequest(CamelModel):
    """
    Matches frontend `SubmitProblemData` exactly.

    The frontend sends camelCase; populate_by_name=True on CamelModel
    means FastAPI will parse both camelCase and snake_case.
    """
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(min_length=1, max_length=5000)
    category: ProblemCategory
    subcategory: str = Field(default="", max_length=200)
    urgency: UrgencyLevel
    affected_population: int = Field(ge=0)      # → affectedPopulation
    location: LocationSchema
    evidence: list[EvidenceSchema] = []
    reporter_name: str = Field(default="Anonymous", max_length=200)  # → reporterName

    @field_validator("location")
    @classmethod
    def validate_location(cls, v: LocationSchema) -> LocationSchema:
        if not (-90 <= v.lat <= 90):
            raise ValueError(f"latitude {v.lat} out of range [-90, 90]")
        if not (-180 <= v.lng <= 180):
            raise ValueError(f"longitude {v.lng} out of range [-180, 180]")
        return v


# ── Filter Query Params ───────────────────────────────────────────────────────

class ProblemFilters(CamelModel):
    """Query parameters for GET /api/problems."""
    category: Optional[str] = None
    district: Optional[str] = None
    search: Optional[str] = None
