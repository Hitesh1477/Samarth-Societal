"""
Dashboard and Analytics domain schemas — Stage 6A.

Matches the frontend contracts in frontend/src/types/index.ts:
  - DashboardStats
  - DashboardData

CamelModel handles camelCase field conversion automatically.
"""

from typing import Optional
from app.schemas.base import CamelModel
from app.schemas.common import MapChallengeSchema


class DashboardStatsSchema(CamelModel):
    """
    Numeric stats matching frontend DashboardStats interface.
    """
    total_reports: int            # → totalReports
    validated_challenges: int     # → validatedChallenges
    high_priority: int            # → highPriority
    active_projects: int          # → activeProjects
    completed_pilots: int         # → completedPilots
    impact_measured: int          # → impactMeasured
    verified_impact_percent: float # → verifiedImpactPercent


class ChartDataPoint(CamelModel):
    """Generic name-value chart data item."""
    name: str
    value: float


class LifecycleDataPoint(CamelModel):
    """Stage-value chart data item for challenge lifecycle."""
    stage: str
    value: float


class DashboardDataSchema(CamelModel):
    """
    Complete dashboard analytics payload matching frontend DashboardData interface.
    """
    stats: DashboardStatsSchema
    challenges_by_category: list[ChartDataPoint]     # → challengesByCategory
    priority_distribution: list[ChartDataPoint]     # → priorityDistribution
    reports_by_district: list[ChartDataPoint]       # → reportsByDistrict
    challenge_lifecycle: list[LifecycleDataPoint]   # → challengeLifecycle
    monthly_reports: list[ChartDataPoint]          # → monthlyReports
    map_challenges: list[MapChallengeSchema]       # → mapChallenges
    ai_insights: list[str]                         # → aiInsights
