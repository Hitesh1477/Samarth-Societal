"""
Projects API router — Stage 4B-A.

Routes:
    POST /api/projects                  → create a project workspace
    GET  /api/projects                  → list projects
    GET  /api/projects/{project_id}     → get project by ID
    PUT  /api/projects/{project_id}     → update project details/status/progress
"""

from fastapi import APIRouter, status

from app.schemas.projects import (
    CreateProjectRequest,
    ProjectSchema,
    UpdateProjectRequest,
)
from app.services import projects as project_service

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post(
    "",
    response_model=ProjectSchema,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project workspace",
    responses={
        201: {"description": "Project created successfully"},
        404: {"description": "Linked challenge not found"},
        500: {"description": "Database error"},
    },
)
async def create_project(body: CreateProjectRequest) -> ProjectSchema:
    """
    Create a project workspace linked to a challenge.

    - Validates that `challenge_id` exists (returns HTTP 404 if not found).
    - Initial status is always PROPOSAL.
    - Initial progress is 0.
    """
    return await project_service.create_project(body)


@router.get(
    "",
    response_model=list[ProjectSchema],
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="List all projects",
)
async def list_projects() -> list[ProjectSchema]:
    """
    Return all project workspaces.
    """
    return await project_service.list_projects()


@router.get(
    "/{project_id}",
    response_model=ProjectSchema,
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="Get project by ID",
    responses={
        404: {"description": "Project not found"},
    },
)
async def get_project(project_id: str) -> ProjectSchema:
    """
    Fetch project details by project ID.
    Returns HTTP 404 for an unknown project ID.
    """
    return await project_service.get_project(project_id)


@router.put(
    "/{project_id}",
    response_model=ProjectSchema,
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="Update project workspace",
    responses={
        404: {"description": "Project not found"},
    },
)
async def update_project(
    project_id: str, body: UpdateProjectRequest
) -> ProjectSchema:
    """
    Update project details, status, or progress.
    Returns HTTP 404 for an unknown project ID.
    """
    return await project_service.update_project(project_id, body)
