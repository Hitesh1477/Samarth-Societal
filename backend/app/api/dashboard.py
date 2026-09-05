"""
Dashboard & Analytics API router — Stage 6A.

Routes:
    GET /api/dashboard/stats → numeric stats summary (DashboardStats)
    GET /api/dashboard       → complete analytics payload (DashboardData)
"""

from fastapi import APIRouter, status

from app.schemas.dashboard import DashboardDataSchema, DashboardStatsSchema
from app.services import dashboard as dashboard_service

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get(
    "/stats",
    response_model=DashboardStatsSchema,
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="Get summary dashboard statistics",
    responses={
        200: {"description": "Dashboard stats retrieved successfully"},
        500: {"description": "Database error"},
    },
)
async def get_dashboard_stats() -> DashboardStatsSchema:
    """
    Return summary statistics matching frontend DashboardStats interface:
    - totalReports
    - validatedChallenges
    - highPriority
    - activeProjects
    - completedPilots
    - impactMeasured
    - verifiedImpactPercent
    """
    return await dashboard_service.get_dashboard_stats()


@router.get(
    "",
    response_model=DashboardDataSchema,
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="Get full dashboard analytics data",
    responses={
        200: {"description": "Dashboard data retrieved successfully"},
        500: {"description": "Database error"},
    },
)
async def get_dashboard_data() -> DashboardDataSchema:
    """
    Return complete dashboard payload matching frontend DashboardData interface:
    - stats
    - challengesByCategory
    - priorityDistribution
    - reportsByDistrict
    - challengeLifecycle
    - monthlyReports
    - mapChallenges
    - aiInsights
    """
    return await dashboard_service.get_dashboard_data()
