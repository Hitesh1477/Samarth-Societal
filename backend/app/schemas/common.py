"""
Common reusable sub-schemas shared across multiple domain schemas.

All field names are in snake_case; the CamelModel base handles camelCase
serialisation automatically.
"""

from typing import Optional
from app.schemas.base import CamelModel
from app.schemas.enums import (
    EvidenceType,
    UserRole,
    SolverType,
    TimelineEventStatus,
    MilestoneStatus,
    PilotStatus,
)


# ── Location ────────────────────────────────────────────────────────────────────

class LocationSchema(CamelModel):
    lat: float
    lng: float
    name: str
    district: str


# ── Evidence ────────────────────────────────────────────────────────────────────

class EvidenceSchema(CamelModel):
    id: str
    type: EvidenceType
    url: str
    name: str


# ── User ────────────────────────────────────────────────────────────────────────

class UserSchema(CamelModel):
    id: str
    name: str
    email: str
    role: UserRole
    avatar_url: Optional[str] = None


# ── Team Member ──────────────────────────────────────────────────────────────────

class TeamMemberSchema(CamelModel):
    id: str
    name: str
    role: str
    avatar_url: Optional[str] = None


# ── Timeline Event ───────────────────────────────────────────────────────────────

class TimelineEventSchema(CamelModel):
    id: str
    label: str
    status: TimelineEventStatus
    date: Optional[str] = None


# ── Priority Breakdown ────────────────────────────────────────────────────────────

class PriorityDimension(CamelModel):
    score: float
    max: float


class PriorityBreakdownSchema(CamelModel):
    safety_risk: PriorityDimension
    population_impact: PriorityDimension
    recurrence: PriorityDimension
    evidence: PriorityDimension
    location_risk: PriorityDimension


# ── Solver Match ──────────────────────────────────────────────────────────────────

class SolverMatchSchema(CamelModel):
    id: str
    name: str
    type: SolverType
    department: Optional[str] = None
    match_score: float          # → matchScore
    reasons: list[str]
    description: str


# ── Milestone ─────────────────────────────────────────────────────────────────────

class MilestoneSchema(CamelModel):
    id: str
    title: str
    status: MilestoneStatus
    progress: float
    due_date: str               # → dueDate
    evidence_count: int         # → evidenceCount


# ── Pilot ─────────────────────────────────────────────────────────────────────────

class PilotSchema(CamelModel):
    challenge_id: str
    status: PilotStatus
    start_date: str
    end_date: Optional[str] = None
    location: str
    participants: int


# ── Impact ───────────────────────────────────────────────────────────────────────

class ImpactMetricSchema(CamelModel):
    id: str
    label: str
    before: float
    after: float
    unit: str
    improvement: float


class ImpactSummarySchema(CamelModel):
    project_id: str             # → projectId
    impact_score: float         # → impactScore
    status: str
    metrics: list[ImpactMetricSchema]
    before_image: str
    after_image: str
    summary: str


# ── Map Challenge ──────────────────────────────────────────────────────────────────

class MapChallengeSchema(CamelModel):
    id: str
    title: str
    lat: float
    lng: float
    priority: float
    priority_level: str         # → priorityLevel
    report_count: int           # → reportCount
    affected_population: int    # → affectedPopulation
    status: str
    category: str
    district: str

