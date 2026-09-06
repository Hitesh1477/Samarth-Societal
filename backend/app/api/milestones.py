"""
Milestones API router — Stage 5A.

Routes:
    GET  /api/projects/{project_id}/milestones → list project milestones
    POST /api/projects/{project_id}/milestones → create milestone for a project
    PUT  /api/milestones/{milestone_id}        → update milestone
"""

from fastapi import APIRouter, status

from app.schemas.milestones import (
    CreateMilestoneRequest,
    MilestoneSchema,
    UpdateMilestoneRequest,
)
from app.services import milestones as milestone_service

router = APIRouter(tags=["milestones"])


@router.get(
    "/api/projects/{project_id}/milestones",
    response_model=list[MilestoneSchema],
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="List milestones for a project",
    responses={404: {"description": "Project not found"}},
)
async def list_milestones(project_id: str) -> list[MilestoneSchema]:
    """Return all milestones belonging to an existing project."""
    return await milestone_service.list_project_milestones_for_api(project_id)


@router.post(
    "/api/projects/{project_id}/milestones",
    response_model=MilestoneSchema,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Create milestone for a project",
    responses={
        201: {"description": "Milestone created successfully"},
        404: {"description": "Project not found"},
        422: {"description": "Validation error"},
    },
)
async def create_milestone(
    project_id: str, body: CreateMilestoneRequest
) -> MilestoneSchema:
    """
    Create a milestone for an existing project workspace.

    - Validates that `project_id` exists (returns HTTP 404 if missing).
    - Progress must be 0–100.
    - Status must be one of: `pending`, `in_progress`, `completed`.
    - Automatically updates parent project progress based on average milestone progress.
    """
    return await milestone_service.create_milestone(project_id, body)


@router.put(
    "/api/milestones/{milestone_id}",
    response_model=MilestoneSchema,
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="Update a milestone",
    responses={
        200: {"description": "Milestone updated successfully"},
        404: {"description": "Milestone not found"},
        422: {"description": "Validation error"},
    },
)
async def update_milestone(
    milestone_id: str, body: UpdateMilestoneRequest
) -> MilestoneSchema:
    """
    Update milestone status, progress, due date, or evidence count.

    - Returns HTTP 404 if `milestone_id` is missing.
    - Validates progress (0–100) and status enum (`pending`, `in_progress`, `completed`).
    - Automatically updates parent project progress based on average milestone progress.
    """
    return await milestone_service.update_milestone(milestone_id, body)
