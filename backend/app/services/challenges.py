"""
Challenge service — Stage 4A.

Implements:
  - create_challenge()          → POST /api/challenges
  - list_challenges()           → GET  /api/challenges
  - get_challenge_detail()      → GET  /api/challenges/{id}

No SQLAlchemy / Alembic — pure Supabase Python client.
Reuses Stage 3A-3D services for priority scoring, solver matching,
and duplicate cluster data where available.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status

from app.core.database import get_supabase_admin_client
from app.schemas.challenges import (
    ChallengeDetailSchema,
    ChallengeEvidenceSchema,
    ChallengeLoc,
    ChallengeSchema,
    CreateChallengeRequest,
    EmbeddedReportSchema,
)
from app.schemas.common import TimelineEventSchema, SolverMatchSchema
from app.schemas.duplicates import DuplicateClusterSchema, DuplicateReportSchema
from app.schemas.enums import ChallengeStatus, PriorityLevel
from app.schemas.priority import PriorityBreakdownSchema, ScoreFactorSchema
from app.services import priority as priority_service
from app.services import matching as matching_service


# ── Helpers ───────────────────────────────────────────────────────────────────

def _db_error(exc: Exception, context: str) -> HTTPException:
    """Wrap unexpected DB errors into a clean HTTP 500."""
    print(f"[DB ERROR] {context}: {exc}")
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="A database error occurred. Please try again later.",
    )


def _row_to_challenge(row: dict) -> ChallengeSchema:
    """Convert a Supabase `challenges` row → ChallengeSchema."""
    return ChallengeSchema(
        id=str(row["id"]),
        title=row["title"],
        description=row.get("description", ""),
        category=row["category"],
        subcategory=row.get("subcategory", ""),
        location=ChallengeLoc(
            lat=float(row.get("lat", 0)),
            lng=float(row.get("lng", 0)),
            name=row.get("location_name", ""),
            district=row.get("district", ""),
        ),
        report_count=int(row.get("report_count", 0)),
        affected_population=int(row.get("affected_population", 0)),
        priority=float(row.get("priority", 0)),
        priority_level=row.get("priority_level", "LOW"),
        status=row.get("status", "NEW"),
        assigned_solver=row.get("assigned_solver"),
        created_at=row["created_at"],
    )


# ── Timeline Builder ──────────────────────────────────────────────────────────

# Ordered lifecycle states
_LIFECYCLE_STEPS: list[tuple[str, ChallengeStatus]] = [
    ("Challenge Created",    ChallengeStatus.NEW),
    ("Under Validation",     ChallengeStatus.UNDER_VALIDATION),
    ("Prioritized",          ChallengeStatus.PRIORITIZED),
    ("Solver Matched",       ChallengeStatus.MATCHED),
    ("Solution Proposed",    ChallengeStatus.SOLUTION_PROPOSED),
    ("Pilot Phase",          ChallengeStatus.PILOT),
    ("Completed",            ChallengeStatus.COMPLETED),
]

_STATUS_ORDER: dict[str, int] = {s.value: i for i, (_, s) in enumerate(_LIFECYCLE_STEPS)}


def build_timeline(current_status: str, created_at: str) -> list[TimelineEventSchema]:
    """
    Build a deterministic timeline for a challenge based on its current status.
    States before the current are 'done', the current is 'current',
    and everything after is 'pending'.
    """
    current_idx = _STATUS_ORDER.get(current_status, 0)
    events: list[TimelineEventSchema] = []

    for step_idx, (label, step_status) in enumerate(_LIFECYCLE_STEPS):
        if step_idx < current_idx:
            ev_status = "done"
            ev_date = created_at  # We only have one reliable timestamp for MVP
        elif step_idx == current_idx:
            ev_status = "current"
            ev_date = created_at
        else:
            ev_status = "pending"
            ev_date = None

        events.append(TimelineEventSchema(
            id=f"tl-{step_status.value.lower().replace('_', '-')}",
            label=label,
            status=ev_status,
            date=ev_date,
        ))

    return events


# ── Fetch Associated Reports ──────────────────────────────────────────────────

def _fetch_associated_reports(client, challenge_id: str) -> list[EmbeddedReportSchema]:
    """Fetch all problems linked to challenge_id, with their evidence."""
    try:
        res = (
            client.table("problems")
            .select("*")
            .eq("challenge_id", challenge_id)
            .order("created_at", desc=False)
            .execute()
        )
        rows = res.data or []
    except Exception as exc:
        print(f"[WARN] Could not fetch reports for challenge {challenge_id}: {exc}")
        return []

    if not rows:
        return []

    problem_ids = [row["id"] for row in rows]

    # Bulk-fetch evidence
    evidence_by_problem: dict[str, list] = {pid: [] for pid in problem_ids}
    try:
        ev_res = (
            client.table("problem_evidence")
            .select("*")
            .in_("problem_id", problem_ids)
            .execute()
        )
        for ev in (ev_res.data or []):
            pid = ev["problem_id"]
            if pid in evidence_by_problem:
                evidence_by_problem[pid].append(ev)
    except Exception as exc:
        print(f"[WARN] Could not fetch evidence in _fetch_associated_reports: {exc}")

    reports: list[EmbeddedReportSchema] = []
    for row in rows:
        ev_list = [
            ChallengeEvidenceSchema(
                id=str(e["id"]),
                type=e["type"],
                url=e["url"],
                name=e.get("name", ""),
            )
            for e in evidence_by_problem.get(row["id"], [])
        ]
        reports.append(EmbeddedReportSchema(
            id=str(row["id"]),
            title=row["title"],
            description=row.get("description", ""),
            category=row["category"],
            subcategory=row.get("subcategory", ""),
            urgency=row.get("urgency", "MEDIUM"),
            affected_population=int(row.get("affected_population", 0)),
            location=ChallengeLoc(
                lat=float(row.get("location_lat", 0)),
                lng=float(row.get("location_lng", 0)),
                name=row.get("location_name", ""),
                district=row.get("location_district", ""),
            ),
            evidence=ev_list,
            status=row.get("status", "SUBMITTED"),
            challenge_id=str(row["challenge_id"]) if row.get("challenge_id") else None,
            similarity=float(row["similarity"]) if row.get("similarity") is not None else None,
            distance=row.get("distance"),
            created_at=row["created_at"],
            reporter_name=row.get("reporter_name", ""),
        ))

    return reports


# ── Priority & Score Helpers ──────────────────────────────────────────────────

def _compute_priority_and_level(
    challenge_id: str,
    title: str,
    description: str,
    affected_population: int,
    report_count: int,
) -> tuple[float, str, PriorityBreakdownSchema, str]:
    """
    Compute priority score and level using Stage 3C engine.
    Returns (priority_float, priority_level_str, breakdown, explanation).
    """
    score_obj = priority_service.build_priority_score(
        target_id=challenge_id,
        title=title,
        description=description,
        urgency="HIGH",
        affected_population=affected_population,
        report_count=report_count,
        evidence_count=min(report_count, 3),
        location_name="",
        district="",
    )
    breakdown = PriorityBreakdownSchema(
        safety_risk=ScoreFactorSchema(
            score=score_obj.breakdown.safety_risk.score,
            max=score_obj.breakdown.safety_risk.max,
        ),
        population_impact=ScoreFactorSchema(
            score=score_obj.breakdown.population_impact.score,
            max=score_obj.breakdown.population_impact.max,
        ),
        recurrence=ScoreFactorSchema(
            score=score_obj.breakdown.recurrence.score,
            max=score_obj.breakdown.recurrence.max,
        ),
        evidence=ScoreFactorSchema(
            score=score_obj.breakdown.evidence.score,
            max=score_obj.breakdown.evidence.max,
        ),
        location_risk=ScoreFactorSchema(
            score=score_obj.breakdown.location_risk.score,
            max=score_obj.breakdown.location_risk.max,
        ),
    )
    return (
        score_obj.total,
        score_obj.level if isinstance(score_obj.level, str) else score_obj.level.value,
        breakdown,
        score_obj.explanation,
    )


# ── Service Functions ─────────────────────────────────────────────────────────

async def create_challenge(data: CreateChallengeRequest) -> ChallengeSchema:
    """
    Create a new unified challenge.
    Computes initial priority score using Stage 3C engine.
    Links to source_problem_id if provided.
    Initial status is always NEW.
    """
    client = get_supabase_admin_client()
    challenge_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    # Compute initial priority score
    priority_val, priority_level_val, _, _ = _compute_priority_and_level(
        challenge_id=challenge_id,
        title=data.title,
        description=data.description,
        affected_population=data.affected_population,
        report_count=1,
    )

    row = {
        "id": challenge_id,
        "title": data.title,
        "description": data.description,
        "category": data.category,
        "subcategory": data.subcategory,
        "district": data.location.district,
        "location_name": data.location.name,
        "lat": data.location.lat,
        "lng": data.location.lng,
        "affected_population": data.affected_population,
        "report_count": 1,
        "priority": priority_val,
        "priority_level": priority_level_val,
        "status": ChallengeStatus.NEW.value,
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    try:
        res = client.table("challenges").insert(row).execute()
    except Exception as exc:
        raise _db_error(exc, "insert challenge")

    if not res.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Challenge creation failed — no data returned from database.",
        )

    inserted = res.data[0]

    # If a source problem is provided, link it to this challenge
    if data.source_problem_id:
        try:
            client.table("problems").update({
                "challenge_id": challenge_id,
                "updated_at": now_iso,
            }).eq("id", data.source_problem_id).execute()
        except Exception as exc:
            print(f"[WARN] Failed to link problem {data.source_problem_id} to challenge {challenge_id}: {exc}")

    return _row_to_challenge(inserted)


async def list_challenges(
    category: Optional[str] = None,
    district: Optional[str] = None,
    priority: Optional[str] = None,
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
) -> list[ChallengeSchema]:
    """
    Fetch all challenges with optional server-side filtering.
    Returns newest first.
    """
    client = get_supabase_admin_client()

    try:
        query = (
            client.table("challenges")
            .select("*")
            .order("created_at", desc=True)
        )

        if category and category.lower() != "all":
            query = query.eq("category", category)

        if district and district.lower() != "all":
            query = query.eq("district", district)

        if priority and priority.lower() != "all":
            query = query.eq("priority_level", priority.upper())

        if status_filter and status_filter.lower() != "all":
            query = query.eq("status", status_filter.upper())

        if search and search.strip():
            search_term = f"%{search.strip()}%"
            query = query.or_(f"title.ilike.{search_term},description.ilike.{search_term}")

        res = query.execute()
    except Exception as exc:
        raise _db_error(exc, "list challenges")

    if not res.data:
        return []

    return [_row_to_challenge(row) for row in res.data]


async def get_challenge_detail(challenge_id: str) -> ChallengeDetailSchema:
    """
    Fetch a single challenge by UUID and enrich it with all available detail:
    - Associated problem reports + evidence
    - Priority breakdown (Stage 3C)
    - Solver matches (Stage 3D)
    - Duplicate cluster summary
    - Deterministic timeline

    Returns HTTP 404 if challenge_id is not found.
    """
    client = get_supabase_admin_client()

    # 1. Fetch the challenge row
    try:
        res = (
            client.table("challenges")
            .select("*")
            .eq("id", challenge_id)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        raise _db_error(exc, f"get challenge {challenge_id}")

    if not res.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Challenge '{challenge_id}' not found.",
        )

    row = res.data[0]

    # 2. Fetch associated reports
    reports = _fetch_associated_reports(client, challenge_id)

    # Collect all evidence across reports
    all_evidence: list[ChallengeEvidenceSchema] = []
    for r in reports:
        all_evidence.extend(r.evidence)

    # 3. Update report_count if DB row is stale
    actual_report_count = max(int(row.get("report_count", 0)), len(reports))
    if actual_report_count == 0:
        actual_report_count = 1  # at least 1 for the challenge itself

    # 4. Compute priority breakdown using Stage 3C engine
    priority_val, priority_level_val, priority_breakdown, priority_explanation = (
        _compute_priority_and_level(
            challenge_id=challenge_id,
            title=row["title"],
            description=row.get("description", ""),
            affected_population=int(row.get("affected_population", 0)),
            report_count=actual_report_count,
        )
    )

    # 5. Fetch solver matches using Stage 3D engine (non-fatal)
    matched_solvers: list[SolverMatchSchema] = []
    try:
        matched_solvers = await matching_service.get_solver_matches_for_challenge(challenge_id)
    except Exception as exc:
        print(f"[WARN] Solver match fetch failed for challenge {challenge_id}: {exc}")

    # 6. Build timeline
    current_status = row.get("status", ChallengeStatus.NEW.value)
    timeline = build_timeline(current_status, row["created_at"])

    # 7. Build duplicate cluster summary from linked reports
    duplicate_reports_schema: list[DuplicateReportSchema] = []
    for r in reports:
        loc_str = r.location.name
        if r.location.district and r.location.district not in loc_str:
            loc_str = f"{loc_str}, {r.location.district}" if loc_str else r.location.district
        duplicate_reports_schema.append(DuplicateReportSchema(
            report_id=r.id,
            title=r.title,
            similarity=float(r.similarity) if r.similarity is not None else 1.0,
            distance=r.distance or "0 m",
            date=r.created_at,
            location=loc_str or "Location",
            reporter=r.reporter_name or "Anonymous",
        ))

    duplicate_cluster = DuplicateClusterSchema(
        problem_id=challenge_id,
        total_reports=actual_report_count,
        similarity=duplicate_reports_schema[0].similarity if duplicate_reports_schema else 1.0,
        reports=duplicate_reports_schema,
        unified_challenge_id=challenge_id,
    )

    # 8. Build and return ChallengeDetailSchema
    return ChallengeDetailSchema(
        # Base Challenge fields
        id=str(row["id"]),
        title=row["title"],
        description=row.get("description", ""),
        category=row["category"],
        subcategory=row.get("subcategory", ""),
        location=ChallengeLoc(
            lat=float(row.get("lat", 0)),
            lng=float(row.get("lng", 0)),
            name=row.get("location_name", ""),
            district=row.get("district", ""),
        ),
        report_count=actual_report_count,
        affected_population=int(row.get("affected_population", 0)),
        priority=priority_val,
        priority_level=priority_level_val,
        status=current_status,
        assigned_solver=row.get("assigned_solver"),
        created_at=row["created_at"],
        # Detail fields
        structured_statement=row.get("description", ""),
        keywords=[],
        confidence=0.85,
        timeline=timeline,
        duplicate_cluster=duplicate_cluster,
        priority_breakdown=priority_breakdown,
        priority_explanation=priority_explanation,
        reports=reports,
        evidence=all_evidence,
        matched_solvers=matched_solvers,
        solution=None,
        pilot=None,
        impact=None,
    )
