"""
Pilot and Impact domain schemas — Stage 5B.

Matches the frontend contracts in frontend/src/types/index.ts:
  - Pilot
  - ImpactMetric
  - ImpactSummary

CamelModel handles camelCase field conversion automatically.
"""

from typing import Optional
from pydantic import Field

from app.schemas.base import CamelModel
from app.schemas.enums import PilotStatus
from app.schemas.common import ImpactMetricSchema, ImpactSummarySchema, PilotSchema


# ── Pilot Requests ────────────────────────────────────────────────────────────

class CreatePilotRequest(CamelModel):
    """
    Payload for POST/PUT pilot endpoint.
    """
    status: Optional[PilotStatus] = Field(default=PilotStatus.PLANNED, description="Pilot status")
    start_date: str = Field(..., min_length=1, description="Pilot start date string")
    end_date: Optional[str] = Field(default=None, description="Pilot end date string")
    location: str = Field(..., min_length=1, description="Pilot location string")
    participants: int = Field(default=0, ge=0, description="Number of participants (non-negative)")


class UpdatePilotRequest(CamelModel):
    """
    Payload for partial updates to a pilot.
    """
    status: Optional[PilotStatus] = Field(None, description="Updated status")
    start_date: Optional[str] = Field(None, description="Updated start date")
    end_date: Optional[str] = Field(None, description="Updated end date")
    location: Optional[str] = Field(None, description="Updated location")
    participants: Optional[int] = Field(None, ge=0, description="Updated participants count")


# ── Impact Requests ───────────────────────────────────────────────────────────

class CreateImpactMetricRequest(CamelModel):
    """
    Payload for POST /api/projects/{project_id}/impact.
    """
    label: str = Field(..., min_length=1, description="Non-empty metric label")
    before: float = Field(..., description="Before value")
    after: float = Field(..., description="After value")
    unit: str = Field(default="", description="Unit of measurement")
    before_image: Optional[str] = Field(default="", description="Before image URL")
    after_image: Optional[str] = Field(default="", description="After image URL")
    summary: Optional[str] = Field(default="", description="Impact summary note")
