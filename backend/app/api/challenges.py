"""
Challenges API router — Stage 4A + existing Stage 3C/3D sub-routes.

Routes implemented in Stage 4A:
    POST /api/challenges                        → create a unified challenge
    GET  /api/challenges                        → list / filter challenges
    GET  /api/challenges/{challenge_id}         → get challenge detail

Routes preserved from Stage 3C/3D:
    GET  /api/challenges/{challenge_id}/priority        → priority score
    GET  /api/challenges/{challenge_id}/solver-matches  → solver matches

Route ordering: specific sub-resource routes MUST be registered BEFORE the
generic /{challenge_id} catch-all to avoid FastAPI path-matching conflicts.
"""

from typing import Optional

from fastapi import APIRouter, Query, status

from app.schemas.challenges import (
    ChallengeDetailSchema,
    ChallengeSchema,
    CreateChallengeRequest,
)
from app.schemas.matching import SolverMatchSchema
from app.schemas.priority import PriorityScoreSchema
from app.services import challenges as challenge_service
from app.services import matching as matching_service
from app.services import priority as priority_service

router = APIRouter(prefix="/api/challenges", tags=["challenges"])


# ── POST /api/challenges ──────────────────────────────────────────────────────

@router.post(
    "",
    response_model=ChallengeSchema,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new unified challenge",
    responses={
        201: {"description": "Challenge created successfully"},
        500: {"description": "Database error"},
    },
)
async def create_challenge(body: CreateChallengeRequest) -> ChallengeSchema:
    """
    Create a unified challenge from a validated/clustered societal problem.

    - Initial status is always NEW.
    - Priority score is computed automatically using the Stage 3C engine.
    - Optionally links to an existing source problem via `sourceProblemId`.
    - Does NOT automatically assign a solver.
    - Does NOT create a project.
    """
    return await challenge_service.create_challenge(body)


# ── GET /api/challenges ───────────────────────────────────────────────────────

@router.get(
    "",
    response_model=list[ChallengeSchema],
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="List / filter challenges",
)
async def list_challenges(
    category: Optional[str] = Query(None, description="Filter by category"),
    district: Optional[str] = Query(None, description="Filter by district"),
    priority: Optional[str] = Query(None, description="Filter by priority level (HIGH|MEDIUM|LOW)"),
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search title and description"),
) -> list[ChallengeSchema]:
    """
    Return all challenges, newest first.

    Supports the same filters the frontend sends:
    - `category`  — ProblemCategory value (or 'all' to skip)
    - `district`  — Exact district name (or 'all' to skip)
    - `priority`  — PriorityLevel value: HIGH | MEDIUM | LOW (or 'all' to skip)
    - `status`    — ChallengeStatus value (or 'all' to skip)
    - `search`    — Case-insensitive substring on title/description
    """
    return await challenge_service.list_challenges(
        category=category,
        district=district,
        priority=priority,
        status_filter=status,
        search=search,
    )


# ── GET /api/challenges/{challenge_id}/priority ────────────────────────────────
# NOTE: Sub-resource routes MUST be before the /{challenge_id} wildcard route.

@router.get(
    "/{challenge_id}/priority",
    response_model=PriorityScoreSchema,
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="Get priority score and breakdown for a challenge or problem",
    responses={
        404: {"description": "Challenge or Problem not found"},
    },
)
async def get_challenge_priority(challenge_id: str) -> PriorityScoreSchema:
    """
    Calculate Stage 3C Priority Score for a unified challenge or problem.
    Returns PriorityScore matching frontend TypeScript contract.
    """
    return await priority_service.get_priority_for_challenge(challenge_id)


# ── GET /api/challenges/{challenge_id}/solver-matches ─────────────────────────

@router.get(
    "/{challenge_id}/solver-matches",
    response_model=list[SolverMatchSchema],
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="Get top solver matches for a challenge",
    responses={
        404: {"description": "Challenge not found"},
    },
)
async def get_solver_matches(challenge_id: str) -> list[SolverMatchSchema]:
    """
    Get top solver matches for a challenge using Stage 3D-A deterministic matching engine.
    Returns list of SolverMatch objects matching frontend TypeScript contract.
    """
    return await matching_service.get_solver_matches_for_challenge(challenge_id)


# ── GET /api/challenges/{challenge_id} ────────────────────────────────────────
# NOTE: This wildcard route MUST be declared AFTER sub-resource routes above.

@router.get(
    "/{challenge_id}",
    response_model=ChallengeDetailSchema,
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="Get challenge detail by ID",
    responses={
        404: {"description": "Challenge not found"},
    },
)
async def get_challenge(challenge_id: str) -> ChallengeDetailSchema:
    """
    Return full ChallengeDetail for a challenge including:
    - Challenge information
    - Associated problem reports + evidence
    - Priority breakdown (Stage 3C)
    - Solver matches (Stage 3D)
    - Duplicate cluster summary
    - Deterministic lifecycle timeline

    Returns HTTP 404 for an unknown challenge ID.
    """
    return await challenge_service.get_challenge_detail(challenge_id)
