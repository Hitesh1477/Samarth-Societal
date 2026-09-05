"""
Pilot & Impact API router — Stage 5B.

Routes:
    POST /api/challenges/{challenge_id}/pilot  → create or update pilot for a challenge/project
    PUT  /api/challenges/{challenge_id}/pilot  → update pilot for a challenge/project
    POST /api/projects/{project_id}/impact     → add impact metric
    GET  /api/projects/{project_id}/impact      → get project impact summary
"""

from fastapi import APIRouter, status

from app.schemas.common import ImpactSummarySchema, PilotSchema
from app.schemas.pilots_impact import CreateImpactMetricRequest, CreatePilotRequest
from app.services import pilots_impact as pilot_impact_service

router = APIRouter(tags=["pilots_impact"])


# ── Pilot Endpoints ───────────────────────────────────────────────────────────

@router.post(
    "/api/challenges/{challenge_id}/pilot",
    response_model=PilotSchema,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Create or update pilot tracking",
    responses={
        201: {"description": "Pilot created/updated successfully"},
        404: {"description": "Challenge/Project not found"},
        422: {"description": "Validation error"},
    },
)
async def create_pilot(
    challenge_id: str, body: CreatePilotRequest
) -> PilotSchema:
    """
    Create or update pilot for a challenge/project.
    - Status must be: `planned`, `active`, `completed`.
    - Participants must be non-negative.
    """
    return await pilot_impact_service.create_or_update_pilot(challenge_id, body)


@router.put(
    "/api/challenges/{challenge_id}/pilot",
    response_model=PilotSchema,
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="Update pilot tracking",
    responses={
        200: {"description": "Pilot updated successfully"},
        404: {"description": "Challenge/Project not found"},
        422: {"description": "Validation error"},
    },
)
async def update_pilot(
    challenge_id: str, body: CreatePilotRequest
) -> PilotSchema:
    """
    Update pilot status, dates, location, or participants.
    """
    return await pilot_impact_service.create_or_update_pilot(challenge_id, body)


# ── Impact Endpoints ──────────────────────────────────────────────────────────

@router.post(
    "/api/projects/{project_id}/impact",
    response_model=ImpactSummarySchema,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Add impact metric to project",
    responses={
        201: {"description": "Impact metric added successfully"},
        404: {"description": "Project not found"},
        422: {"description": "Validation error"},
    },
)
async def add_impact_metric(
    project_id: str, body: CreateImpactMetricRequest
) -> ImpactSummarySchema:
    """
    Add an impact metric (before/after values, label, unit) to a project workspace.
    Returns the updated ImpactSummary including metric improvements and overall impactScore.
    """
    return await pilot_impact_service.add_impact_metric(project_id, body)


@router.get(
    "/api/projects/{project_id}/impact",
    response_model=ImpactSummarySchema,
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="Get project impact summary",
    responses={
        200: {"description": "Impact summary fetched successfully"},
        404: {"description": "Project not found"},
    },
)
async def get_project_impact(project_id: str) -> ImpactSummarySchema:
    """
    Fetch impact summary for a project workspace.
    If no impact metrics exist, returns a valid empty/pending response (`status: 'pending'`, `impactScore: 0.0`).
    Returns HTTP 404 for an unknown project ID.
    """
    return await pilot_impact_service.get_project_impact(project_id)
