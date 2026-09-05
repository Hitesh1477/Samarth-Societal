"""
Dashboard & Analytics service — Stage 6A.

Implements:
  - get_dashboard_stats() → GET /api/dashboard/stats
  - get_dashboard_data()  → GET /api/dashboard

Calculates real statistics from Supabase database tables:
  - problems
  - challenges
  - projects
  - pilots
  - impact_metrics
"""

from collections import Counter
from datetime import datetime
from typing import Any

from app.core.database import get_supabase_admin_client
from app.schemas.common import MapChallengeSchema
from app.schemas.dashboard import (
    ChartDataPoint,
    DashboardDataSchema,
    DashboardStatsSchema,
    LifecycleDataPoint,
)
from app.services import challenges as challenge_service
from app.services import projects as project_service
from app.services import pilots_impact as pilot_impact_service


async def get_dashboard_stats() -> DashboardStatsSchema:
    """
    Calculate and return live DashboardStats from database.
    """
    client = get_supabase_admin_client()

    # 1. total_reports: count of records in `problems`
    total_reports = 0
    try:
        res = client.table("problems").select("id", count="exact").execute()
        total_reports = res.count if res.count is not None else len(res.data or [])
    except Exception as exc:
        print(f"[DASHBOARD SERVICE] Count problems error: {exc}")

    # 2. validated_challenges & high_priority: count of records in `challenges`
    validated_challenges = 0
    high_priority = 0
    challenges_rows: list[dict] = []
    try:
        res = client.table("challenges").select("*").execute()
        challenges_rows = res.data or []
        validated_challenges = len(challenges_rows)
        high_priority = sum(
            1 for c in challenges_rows
            if str(c.get("priority_level", "")).upper() == "HIGH" or float(c.get("priority", 0)) >= 70
        )
    except Exception as exc:
        print(f"[DASHBOARD SERVICE] Query challenges error: {exc}")

    # 3. active_projects: count of projects with status = 'ACTIVE' or 'PROPOSAL' or 'PILOT'
    active_projects = 0
    try:
        projects_list = await project_service.list_projects()
        active_projects = sum(
            1 for p in projects_list
            if str(p.status.value if hasattr(p.status, "value") else p.status).upper() in ["ACTIVE", "PROPOSAL", "PILOT"]
        )
    except Exception as exc:
        print(f"[DASHBOARD SERVICE] Count active projects error: {exc}")

    # 4. completed_pilots: count of pilots with status = 'completed'
    completed_pilots = 0
    try:
        res = client.table("pilots").select("*").execute()
        if res.data:
            completed_pilots = sum(
                1 for p in res.data
                if str(p.get("status", "")).lower() == "completed"
            )
    except Exception as exc:
        print(f"[DASHBOARD SERVICE] Count pilots error: {exc}")

    # 5. impact_measured & verified_impact_percent: count of projects with impact metrics
    impact_measured = 0
    verified_impact_percent = 0.0
    try:
        res = client.table("impact_metrics").select("project_id").execute()
        if res.data:
            proj_ids = set(str(r["project_id"]) for r in res.data if r.get("project_id"))
            impact_measured = len(proj_ids)
            if active_projects > 0:
                verified_impact_percent = round((impact_measured / active_projects) * 100.0, 1)
            elif impact_measured > 0:
                verified_impact_percent = 100.0
    except Exception as exc:
        print(f"[DASHBOARD SERVICE] Query impact error: {exc}")

    return DashboardStatsSchema(
        total_reports=total_reports,
        validated_challenges=validated_challenges,
        high_priority=high_priority,
        active_projects=active_projects,
        completed_pilots=completed_pilots,
        impact_measured=impact_measured,
        verified_impact_percent=verified_impact_percent,
    )


async def get_dashboard_data() -> DashboardDataSchema:
    """
    Build full dashboard analytics payload including stats, chart data, map challenges, and AI insights.
    """
    stats = await get_dashboard_stats()
    client = get_supabase_admin_client()

    # 1. Fetch raw problems & challenges for analytics
    problems_rows: list[dict] = []
    try:
        res = client.table("problems").select("*").execute()
        problems_rows = res.data or []
    except Exception as exc:
        print(f"[DASHBOARD SERVICE] Fetch problems error: {exc}")

    challenges_rows: list[dict] = []
    try:
        res = client.table("challenges").select("*").execute()
        challenges_rows = res.data or []
    except Exception as exc:
        print(f"[DASHBOARD SERVICE] Fetch challenges error: {exc}")

    # 2. challengesByCategory
    cat_counts = Counter(str(c.get("category", "Other")) for c in challenges_rows)
    if not cat_counts and problems_rows:
        cat_counts = Counter(str(p.get("category", "Other")) for p in problems_rows)
    challenges_by_category = [
        ChartDataPoint(name=cat, value=float(count))
        for cat, count in cat_counts.items()
    ]

    # 3. priorityDistribution
    prio_counts = Counter(str(c.get("priority_level", "MEDIUM")).upper() for c in challenges_rows)
    if not prio_counts:
        prio_counts = Counter({"HIGH": 0, "MEDIUM": 0, "LOW": 0})
    priority_distribution = [
        ChartDataPoint(name=level, value=float(prio_counts.get(level, 0)))
        for level in ["HIGH", "MEDIUM", "LOW"]
    ]

    # 4. reportsByDistrict
    dist_counts = Counter(
        str(p.get("location_district") or p.get("district") or "Unknown") for p in problems_rows
    )
    if not dist_counts and challenges_rows:
        dist_counts = Counter(str(c.get("district", "Unknown")) for c in challenges_rows)
    reports_by_district = [
        ChartDataPoint(name=dist, value=float(count))
        for dist, count in dist_counts.items()
    ]

    # 5. challengeLifecycle
    stage_counts = Counter(str(c.get("status", "NEW")).upper() for c in challenges_rows)
    lifecycle_stages = ["NEW", "UNDER_VALIDATION", "PRIORITIZED", "MATCHED", "SOLUTION_PROPOSED", "PILOT", "COMPLETED"]
    challenge_lifecycle = [
        LifecycleDataPoint(stage=st, value=float(stage_counts.get(st, 0)))
        for st in lifecycle_stages
    ]

    # 6. monthlyReports
    month_counts: Counter = Counter()
    for p in problems_rows:
        created_at_str = p.get("created_at")
        if created_at_str:
            try:
                dt = datetime.fromisoformat(str(created_at_str).replace("Z", "+00:00"))
                month_key = dt.strftime("%b %Y")
                month_counts[month_key] += 1
            except Exception:
                pass
    monthly_reports = [
        ChartDataPoint(name=m, value=float(cnt))
        for m, cnt in month_counts.items()
    ]

    # 7. mapChallenges
    map_challenges = [
        MapChallengeSchema(
            id=str(c["id"]),
            title=str(c.get("title", "")),
            lat=float(c.get("lat", 0.0)),
            lng=float(c.get("lng", 0.0)),
            priority=float(c.get("priority", 50.0)),
            priority_level=str(c.get("priority_level", "MEDIUM")),
            report_count=int(c.get("report_count", 1)),
            affected_population=int(c.get("affected_population", 0)),
            status=str(c.get("status", "NEW")),
            category=str(c.get("category", "Other")),
            district=str(c.get("district", "")),
        )
        for c in challenges_rows
    ]

    # 8. Deterministic AI Insights
    ai_insights = []
    if stats.high_priority > 0:
        ai_insights.append(f"{stats.high_priority} high-priority societal challenges require immediate resource allocation.")
    if stats.total_reports > 0:
        top_cat = cat_counts.most_common(1)[0][0] if cat_counts else "Infrastructure"
        ai_insights.append(f"Highest report concentration observed in '{top_cat}' sector across active districts.")
    if stats.active_projects > 0:
        ai_insights.append(f"{stats.active_projects} active solution projects currently deployed in innovation pipeline.")
    if not ai_insights:
        ai_insights = [
            "Platform initialized. Submit societal problem reports to trigger automated AI clustering and priority scoring.",
            "No active critical alerts detected across registered municipal districts.",
        ]

    return DashboardDataSchema(
        stats=stats,
        challenges_by_category=challenges_by_category,
        priority_distribution=priority_distribution,
        reports_by_district=reports_by_district,
        challenge_lifecycle=challenge_lifecycle,
        monthly_reports=monthly_reports,
        map_challenges=map_challenges,
        ai_insights=ai_insights,
    )
