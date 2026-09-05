"""
Project domain schemas — Stage 4B-A.

Matches the frontend Project contract in frontend/src/types/index.ts:

export interface Project {
  id: string;
  challengeId: string;
  challengeTitle: string;
  title: string;
  status: 'PROPOSAL' | 'ACTIVE' | 'PILOT' | 'COMPLETED';
  progress: number;
  team: TeamMember[];
  facultyMentor: string;
  industryPartner: string;
  createdAt: string;
}

CamelModel serialises all snake_case fields to camelCase automatically.
"""

from typing import Optional
from pydantic import Field

from app.schemas.base import CamelModel
from app.schemas.common import TeamMemberSchema
from app.schemas.enums import ProjectStatus


class CreateProjectRequest(CamelModel):
    """
    Payload for POST /api/projects.
    challenge_id is required and must link to an existing challenge.
    """
    challenge_id: str = Field(..., description="ID of the associated challenge")
    title: str = Field(..., min_length=3, description="Project title")
    description: Optional[str] = Field(None, description="Project description")
    team: list[TeamMemberSchema] = Field(default_factory=list, description="Team members")
    faculty_mentor: str = Field(default="", description="Faculty mentor name")
    industry_partner: str = Field(default="", description="Industry partner name")


class UpdateProjectRequest(CamelModel):
    """
    Payload for PUT /api/projects/{project_id}.
    All fields are optional for partial updates.
    """
    title: Optional[str] = Field(None, min_length=3, description="Updated project title")
    description: Optional[str] = Field(None, description="Updated project description")
    status: Optional[ProjectStatus] = Field(None, description="Updated project status")
    progress: Optional[float] = Field(None, ge=0, le=100, description="Updated progress percentage (0-100)")
    team: Optional[list[TeamMemberSchema]] = Field(None, description="Updated team members")
    faculty_mentor: Optional[str] = Field(None, description="Updated faculty mentor")
    industry_partner: Optional[str] = Field(None, description="Updated industry partner")


class ProjectSchema(CamelModel):
    """
    Response schema for Project object matching frontend TypeScript interface.
    """
    id: str
    challenge_id: str
    challenge_title: str
    title: str
    status: ProjectStatus
    progress: float
    team: list[TeamMemberSchema]
    faculty_mentor: str
    industry_partner: str
    created_at: str
