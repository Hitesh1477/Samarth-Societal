"""
Milestone domain schemas — Stage 5A.

Matches the frontend Milestone contract in frontend/src/types/index.ts:

export interface Milestone {
  id: string;
  title: string;
  status: 'pending' | 'in_progress' | 'completed';
  progress: number;
  dueDate: string;
  evidenceCount: number;
}

CamelModel serialises all snake_case fields to camelCase automatically.
"""

from typing import Optional
from pydantic import Field

from app.schemas.base import CamelModel
from app.schemas.enums import MilestoneStatus


class CreateMilestoneRequest(CamelModel):
    """
    Payload for POST /api/projects/{project_id}/milestones.
    """
    title: str = Field(..., min_length=2, description="Milestone title")
    status: Optional[MilestoneStatus] = Field(default=MilestoneStatus.PENDING, description="Initial milestone status")
    progress: Optional[float] = Field(default=0.0, ge=0.0, le=100.0, description="Initial progress (0-100)")
    due_date: Optional[str] = Field(default="", description="Due date string")
    evidence_count: Optional[int] = Field(default=0, ge=0, description="Attached evidence count")


class UpdateMilestoneRequest(CamelModel):
    """
    Payload for PUT /api/milestones/{milestone_id}.
    All fields are optional for partial updates.
    """
    title: Optional[str] = Field(None, min_length=2, description="Updated milestone title")
    status: Optional[MilestoneStatus] = Field(None, description="Updated milestone status")
    progress: Optional[float] = Field(None, ge=0.0, le=100.0, description="Updated progress (0-100)")
    due_date: Optional[str] = Field(None, description="Updated due date string")
    evidence_count: Optional[int] = Field(None, ge=0, description="Updated evidence count")


class MilestoneSchema(CamelModel):
    """
    Response schema for Milestone object matching frontend TypeScript contract.
    """
    id: str
    title: str
    status: MilestoneStatus
    progress: float
    due_date: str
    evidence_count: int
