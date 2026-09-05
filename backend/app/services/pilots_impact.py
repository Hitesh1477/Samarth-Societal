"""
Pilot & Impact tracking service — Stage 5B.

Implements:
  PART A: Pilot tracking (create/update pilot for a project or challenge)
    - create_or_update_pilot()

  PART B: Impact tracking (metrics & summary)
    - add_impact_metric()      → POST /api/projects/{project_id}/impact
    - get_project_impact()     → GET  /api/projects/{project_id}/impact

Uses Supabase Python client with in-memory fallback.
Calculates improvement and impactScore deterministically without LLMs.
"""

import uuid
from typing import Optional

from fastapi import HTTPException, status

from app.core.database import get_supabase_admin_client
from app.schemas.common import ImpactMetricSchema, ImpactSummarySchema, PilotSchema
from app.schemas.enums import PilotStatus
from app.schemas.pilots_impact import CreateImpactMetricRequest, CreatePilotRequest
from app.services import challenges as challenge_service
from app.services import projects as project_service

# In-memory stores fallback if tables are missing in Supabase
_MEMORY_PILOTS: dict[str, dict] = {}          # key = challenge_id
_MEMORY_IMPACT_METRICS: dict[str, list] = {}  # key = project_id
_MEMORY_IMPACT_META: dict[str, dict] = {}     # key = project_id


# ── PART A: PILOT SERVICE ──────────────────────────────────────────────────────

async def create_or_update_pilot(challenge_id: str, payload: CreatePilotRequest) -> PilotSchema:
    """
    Create or update a pilot for a challenge.
    Validates challenge existence (returns HTTP 404 if challenge is not found).
    """
    # Verify challenge exists
    try:
        await challenge_service.get_challenge_detail(challenge_id)
    except HTTPException:
        # Check if project exists by challenge_id or direct project ID fallback
        client = get_supabase_admin_client()
        try:
            res = client.table("challenges").select("id").eq("id", challenge_id).limit(1).execute()
            if not res.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Challenge or Project '{challenge_id}' not found.",
                )
        except HTTPException:
            raise
        except Exception:
            pass

    st_val = payload.status.value if hasattr(payload.status, "value") else str(payload.status or "planned")

    pilot_dict = {
        "challenge_id": challenge_id,
        "status": st_val,
        "start_date": payload.start_date,
        "end_date": payload.end_date,
        "location": payload.location,
        "participants": payload.participants,
    }

    client = get_supabase_admin_client()
    try:
        res = client.table("pilots").upsert(pilot_dict).execute()
        if res.data:
            d = res.data[0]
            return PilotSchema(
                challenge_id=str(d.get("challenge_id")),
                status=PilotStatus(str(d.get("status", "planned"))),
                start_date=str(d.get("start_date", "")),
                end_date=d.get("end_date"),
                location=str(d.get("location", "")),
                participants=int(d.get("participants", 0)),
            )
    except Exception as exc:
        print(f"[PILOT SERVICE] Supabase upsert fallback to memory: {exc}")

    _MEMORY_PILOTS[challenge_id] = pilot_dict
    return PilotSchema(
        challenge_id=challenge_id,
        status=PilotStatus(st_val),
        start_date=payload.start_date,
        end_date=payload.end_date,
        location=payload.location,
        participants=payload.participants,
    )


async def get_pilot(challenge_id: str) -> Optional[PilotSchema]:
    """Internal helper to get pilot by challenge ID."""
    client = get_supabase_admin_client()
    try:
        res = client.table("pilots").select("*").eq("challenge_id", challenge_id).limit(1).execute()
        if res.data:
            d = res.data[0]
            return PilotSchema(
                challenge_id=str(d.get("challenge_id")),
                status=PilotStatus(str(d.get("status", "planned"))),
                start_date=str(d.get("start_date", "")),
                end_date=d.get("end_date"),
                location=str(d.get("location", "")),
                participants=int(d.get("participants", 0)),
            )
    except Exception:
        pass

    if challenge_id in _MEMORY_PILOTS:
        p = _MEMORY_PILOTS[challenge_id]
        return PilotSchema(
            challenge_id=challenge_id,
            status=PilotStatus(str(p.get("status", "planned"))),
            start_date=str(p.get("start_date", "")),
            end_date=p.get("end_date"),
            location=str(p.get("location", "")),
            participants=int(p.get("participants", 0)),
        )
    return None


# ── PART B & C: IMPACT METRICS SERVICE ───────────────────────────────────────

def _calc_improvement(before: float, after: float) -> float:
    """
    Calculate percentage improvement deterministically.
    Handles cases where before is 0.
    """
    if before == 0:
        return 100.0 if after > 0 else 0.0
    return round(((after - before) / abs(before)) * 100.0, 1)


def _calc_impact_score(metrics: list[ImpactMetricSchema]) -> float:
    """
    Calculate a simple deterministic impactScore (0-100) from metrics.
    Takes the average absolute improvement capped at 100, or 0 if no metrics.
    """
    if not metrics:
        return 0.0
    improvements = [abs(m.improvement) for m in metrics]
    avg_imp = sum(improvements) / len(improvements)
    return round(min(100.0, avg_imp), 1)


async def add_impact_metric(project_id: str, payload: CreateImpactMetricRequest) -> ImpactSummarySchema:
    """
    Add an impact metric to a project workspace.
    Validates project existence (returns HTTP 404 if project is missing).
    Recalculates improvement & overall impactScore.
    """
    # Verify project exists first
    project = await project_service.get_project(project_id)

    metric_id = str(uuid.uuid4())
    improvement = _calc_improvement(payload.before, payload.after)

    metric_dict = {
        "id": metric_id,
        "project_id": project.id,
        "label": payload.label,
        "before": payload.before,
        "after": payload.after,
        "unit": payload.unit or "",
        "improvement": improvement,
    }

    client = get_supabase_admin_client()
    try:
        client.table("impact_metrics").insert(metric_dict).execute()
    except Exception as exc:
        print(f"[IMPACT SERVICE] Supabase metric insert fallback to memory: {exc}")

    if project_id not in _MEMORY_IMPACT_METRICS:
        _MEMORY_IMPACT_METRICS[project_id] = []
    _MEMORY_IMPACT_METRICS[project_id].append(metric_dict)

    if payload.before_image or payload.after_image or payload.summary:
        meta = _MEMORY_IMPACT_META.get(project_id, {})
        if payload.before_image:
            meta["before_image"] = payload.before_image
        if payload.after_image:
            meta["after_image"] = payload.after_image
        if payload.summary:
            meta["summary"] = payload.summary
        _MEMORY_IMPACT_META[project_id] = meta

    return await get_project_impact(project_id)


async def get_project_impact(project_id: str) -> ImpactSummarySchema:
    """
    Fetch impact summary for a project.
    Validates project existence (returns HTTP 404 if project not found).
    If no impact metrics exist, returns clean empty/pending summary rather than crashing.
    """
    # Verify project exists first
    project = await project_service.get_project(project_id)

    metrics_list: list[ImpactMetricSchema] = []
    before_image = ""
    after_image = ""
    summary_text = ""

    client = get_supabase_admin_client()
    try:
        res = client.table("impact_metrics").select("*").eq("project_id", project_id).execute()
        if res.data:
            for row in res.data:
                b = float(row.get("before", 0.0))
                a = float(row.get("after", 0.0))
                imp = float(row.get("improvement") if row.get("improvement") is not None else _calc_improvement(b, a))
                metrics_list.append(
                    ImpactMetricSchema(
                        id=str(row["id"]),
                        label=str(row.get("label", "")),
                        before=b,
                        after=a,
                        unit=str(row.get("unit", "")),
                        improvement=imp,
                    )
                )
    except Exception as exc:
        print(f"[IMPACT SERVICE] Supabase select fallback to memory: {exc}")

    if not metrics_list and project_id in _MEMORY_IMPACT_METRICS:
        for row in _MEMORY_IMPACT_METRICS[project_id]:
            b = float(row.get("before", 0.0))
            a = float(row.get("after", 0.0))
            imp = float(row.get("improvement") if row.get("improvement") is not None else _calc_improvement(b, a))
            metrics_list.append(
                ImpactMetricSchema(
                    id=str(row["id"]),
                    label=str(row.get("label", "")),
                    before=b,
                    after=a,
                    unit=str(row.get("unit", "")),
                    improvement=imp,
                )
            )

    meta = _MEMORY_IMPACT_META.get(project_id, {})
    before_image = meta.get("before_image", "")
    after_image = meta.get("after_image", "")
    summary_text = meta.get("summary", "")

    impact_score = _calc_impact_score(metrics_list)
    impact_status = "measured" if metrics_list else "pending"

    return ImpactSummarySchema(
        project_id=project.id,
        impact_score=impact_score,
        status=impact_status,
        metrics=metrics_list,
        before_image=before_image,
        after_image=after_image,
        summary=summary_text,
    )
