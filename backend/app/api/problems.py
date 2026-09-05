"""
Problem API router.

Routes implemented in Stage 2:
    POST /api/problems          → submit a new problem report
    GET  /api/problems          → list / filter problem reports
    GET  /api/problems/{id}     → get a single problem report

Routes reserved for Stage 3 (NOT implemented here):
    POST /api/problems/{id}/analyze
    GET  /api/problems/{id}/duplicates
"""

from fastapi import APIRouter, HTTPException, Query, status
from typing import Optional

from app.schemas.ai import AIAnalysisSchema
from app.schemas.duplicates import DuplicateClusterSchema
from app.schemas.priority import PriorityScoreSchema
from app.schemas.problems import ProblemReportSchema, SubmitProblemRequest
from app.services import duplicates as duplicate_service
from app.services import priority as priority_service
from app.services import problems as problem_service

router = APIRouter(prefix="/api/problems", tags=["problems"])





# ── POST /api/problems ────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=ProblemReportSchema,
    response_model_by_alias=True,       # ensures camelCase in response JSON
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new problem report",
)
async def submit_problem(body: SubmitProblemRequest) -> ProblemReportSchema:
    """
    Accept a citizen problem report, persist it to Supabase, and return the
    saved record in the exact format the frontend expects.

    Validates:
    - title / description not empty
    - affectedPopulation >= 0
    - lat in [-90, 90], lng in [-180, 180]
    - category is a known ProblemCategory value
    - urgency is a known UrgencyLevel value
    """
    return await problem_service.create_problem(body)


# ── GET /api/problems ─────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=list[ProblemReportSchema],
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="List / filter problem reports",
)
async def list_problems(
    category: Optional[str] = Query(None, description="Filter by problem category"),
    district: Optional[str] = Query(None, description="Filter by district name"),
    search:   Optional[str] = Query(None, description="Search title and description"),
) -> list[ProblemReportSchema]:
    """
    Return all problem reports, newest first.

    Supports the same filters the frontend sends:
    - `category` — must match a valid ProblemCategory value (or 'all' to skip)
    - `district`  — exact match on location district (or 'all' to skip)
    - `search`    — case-insensitive substring match on title and description
    """
    return await problem_service.list_problems(
        category=category,
        district=district,
        search=search,
    )


# ── GET /api/problems/{id} ────────────────────────────────────────────────────

@router.get(
    "/{problem_id}",
    response_model=ProblemReportSchema,
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="Get a single problem report by ID",
    responses={
        404: {"description": "Problem not found"},
    },
)
async def get_problem(problem_id: str) -> ProblemReportSchema:
    """
    Return one complete problem report including its evidence list.
    Returns HTTP 404 with a JSON body if the problem does not exist.
    """
    return await problem_service.get_problem(problem_id)


# ── POST /api/problems/{id}/analyze ──────────────────────────────────────────

@router.post(
    "/{problem_id}/analyze",
    response_model=AIAnalysisSchema,
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="Analyze a problem report using AI",
    responses={
        404: {"description": "Problem not found"},
    },
)
async def analyze_problem(problem_id: str) -> AIAnalysisSchema:
    """
    Perform Stage 3A AI Problem Analysis on a citizen report.
    Returns AIAnalysis matching frontend TypeScript contract.
    """
    return await problem_service.analyze_problem(problem_id)


# ── GET /api/problems/{id}/duplicates ───────────────────────────────────────

@router.get(
    "/{problem_id}/duplicates",
    response_model=DuplicateClusterSchema,
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="Get related duplicate reports and cluster info for a problem",
    responses={
        404: {"description": "Problem not found"},
    },
)
async def get_problem_duplicates(problem_id: str) -> DuplicateClusterSchema:
    """
    Perform Stage 3B Duplicate Detection and Cluster retrieval.
    Returns DuplicateCluster matching frontend TypeScript contract.
    """
    return await duplicate_service.get_duplicate_cluster(problem_id)


# ── GET /api/problems/{id}/priority ──────────────────────────────────────────

@router.get(
    "/{problem_id}/priority",
    response_model=PriorityScoreSchema,
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="Get priority score and breakdown for a problem",
    responses={
        404: {"description": "Problem not found"},
    },
)
async def get_problem_priority(problem_id: str) -> PriorityScoreSchema:
    """
    Calculate Stage 3C Priority Score for a problem.
    Returns PriorityScore matching frontend TypeScript contract.
    """
    return await priority_service.get_priority_for_challenge(problem_id)



