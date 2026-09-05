"""
Challenge domain schemas — Stage 4A.

Matches the frontend TypeScript interfaces exactly:
  - Challenge         (frontend/src/types/index.ts)
  - ChallengeDetail   (frontend/src/types/index.ts)

All fields are snake_case internally; CamelModel serialises them to camelCase
on the wire via alias_generator=to_camel.
"""

from typing import Optional
from pydantic import Field

from app.schemas.base import CamelModel
from app.schemas.enums import (
    ChallengeStatus,
    PriorityLevel,
    ProblemCategory,
)
from app.schemas.common import (
    TimelineEventSchema,
    SolverMatchSchema,
    PilotSchema,
    ImpactSummarySchema,
)
from app.schemas.duplicates import DuplicateClusterSchema
from app.schemas.priority import PriorityBreakdownSchema


# ── Nested location (re-declared to stay self-contained) ──────────────────────

class ChallengeLoc(CamelModel):
    """Location sub-object matching frontend Challenge.location."""
    lat: float
    lng: float
    name: str
    district: str


# ── Evidence (reused from common shape) ──────────────────────────────────────

class ChallengeEvidenceSchema(CamelModel):
    """Evidence item attached to a challenge (via its constituent reports)."""
    id: str
    type: str          # 'image' | 'audio' | 'document'
    url: str
    name: str


# ── Minimal problem report embedded inside ChallengeDetail ───────────────────

class EmbeddedReportSchema(CamelModel):
    """
    Minimal ProblemReport embedded inside ChallengeDetail.reports.
    Matches frontend ProblemReport (subset sufficient for the UI).
    """
    id: str
    title: str
    description: str
    category: str
    subcategory: str
    urgency: str
    affected_population: int = Field(ge=0)
    location: ChallengeLoc
    evidence: list[ChallengeEvidenceSchema] = Field(default_factory=list)
    status: str
    challenge_id: Optional[str] = None
    similarity: Optional[float] = None
    distance: Optional[str] = None
    created_at: str
    reporter_name: str


# ── Solution (for ChallengeDetail.solution) ───────────────────────────────────

class TeamMemberSchema(CamelModel):
    id: str
    name: str
    role: str
    avatar_url: Optional[str] = None


class MilestoneSchema(CamelModel):
    id: str
    title: str
    status: str          # 'pending' | 'in_progress' | 'completed'
    progress: float
    due_date: str
    evidence_count: int


class SolutionSchema(CamelModel):
    challenge_id: str
    summary: str
    approach: str
    team_members: list[TeamMemberSchema] = Field(default_factory=list)
    faculty_mentor: str
    industry_partner: str
    milestones: list[MilestoneSchema] = Field(default_factory=list)
    progress: float


# ── Challenge (matches frontend Challenge interface) ──────────────────────────

class ChallengeSchema(CamelModel):
    """
    Matches frontend `Challenge` interface exactly.

    camelCase aliases (via CamelModel):
        reportCount, affectedPopulation, priorityLevel,
        assignedSolver, createdAt
    """
    id: str
    title: str
    category: str                        # ProblemCategory value
    subcategory: str
    location: ChallengeLoc
    report_count: int = Field(ge=0)      # → reportCount
    affected_population: int = Field(ge=0)  # → affectedPopulation
    priority: float = Field(ge=0.0, le=100.0)
    priority_level: str                  # → priorityLevel  ('HIGH'|'MEDIUM'|'LOW')
    status: str                          # → ChallengeStatus value
    assigned_solver: Optional[str] = None  # → assignedSolver
    created_at: str                      # → createdAt
    description: str


# ── ChallengeDetail (matches frontend ChallengeDetail interface) ──────────────

class ChallengeDetailSchema(ChallengeSchema):
    """
    Extends ChallengeSchema with all the rich detail fields.

    camelCase aliases (via CamelModel):
        structuredStatement, keywords, confidence, timeline,
        duplicateCluster, priorityBreakdown, priorityExplanation,
        reports, evidence, matchedSolvers, solution, pilot, impact
    """
    structured_statement: str = ""         # → structuredStatement
    keywords: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    timeline: list[TimelineEventSchema] = Field(default_factory=list)
    duplicate_cluster: Optional[DuplicateClusterSchema] = None  # → duplicateCluster
    priority_breakdown: Optional[PriorityBreakdownSchema] = None  # → priorityBreakdown
    priority_explanation: str = ""          # → priorityExplanation
    reports: list[EmbeddedReportSchema] = Field(default_factory=list)
    evidence: list[ChallengeEvidenceSchema] = Field(default_factory=list)
    matched_solvers: list[SolverMatchSchema] = Field(default_factory=list)  # → matchedSolvers
    solution: Optional[SolutionSchema] = None
    pilot: Optional[PilotSchema] = None
    impact: Optional[ImpactSummarySchema] = None


# ── Request Body for POST /api/challenges ─────────────────────────────────────

class CreateChallengeRequest(CamelModel):
    """
    Request body for POST /api/challenges.
    Accepts the fields required to create a Challenge and optionally link it
    to an existing problem or cluster.
    """
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(default="", max_length=5000)
    category: str
    subcategory: str = Field(default="")
    location: ChallengeLoc
    affected_population: int = Field(ge=0, default=0)
    # Optional link to a source problem or primary problem in the cluster
    source_problem_id: Optional[str] = None   # → sourceProblemId


# ── Filters for GET /api/challenges ──────────────────────────────────────────

class ChallengeFilters(CamelModel):
    """Query parameters for GET /api/challenges (mirrors frontend ProblemFilters)."""
    category: Optional[str] = None
    district: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    search: Optional[str] = None
