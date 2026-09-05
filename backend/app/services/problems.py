"""
Problem service — all Supabase database operations for the problem domain.

Uses the admin (service-role) client for server-side operations so RLS
does not block inserts/updates from the backend.

No SQLAlchemy. Pure Supabase Python client.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status

from app.core.database import get_supabase_admin_client
from app.schemas.ai import AIAnalysisSchema
from app.schemas.enums import ProblemStatus
from app.schemas.problems import (
    EvidenceSchema,
    LocationSchema,
    ProblemReportSchema,
    SubmitProblemRequest,
)
from app.services.ai_provider import analyze_problem_with_ai



# ── Helpers ───────────────────────────────────────────────────────────────────

def _row_to_problem_report(row: dict, evidence: list[dict]) -> ProblemReportSchema:
    """Convert a Supabase `problems` row + evidence list → ProblemReportSchema."""
    return ProblemReportSchema(
        id=str(row["id"]),
        title=row["title"],
        description=row["description"],
        category=row["category"],
        subcategory=row.get("subcategory", ""),
        urgency=row["urgency"],
        affected_population=row["affected_population"],
        location=LocationSchema(
            lat=row["location_lat"],
            lng=row["location_lng"],
            name=row.get("location_name", ""),
            district=row.get("location_district", ""),
        ),
        evidence=[
            EvidenceSchema(
                id=str(e["id"]),
                type=e["type"],
                url=e["url"],
                name=e.get("name", ""),
            )
            for e in evidence
        ],
        status=row["status"],
        challenge_id=str(row["challenge_id"]) if row.get("challenge_id") else None,
        similarity=float(row["similarity"]) if row.get("similarity") is not None else None,
        distance=row.get("distance"),
        created_at=row["created_at"],
        reporter_name=row.get("reporter_name", ""),
    )


def _db_error(exc: Exception, context: str) -> HTTPException:
    """Wrap a Supabase / unexpected error into a clean 500."""
    # Do NOT expose internal details — log them server-side only
    print(f"[DB ERROR] {context}: {exc}")
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="A database error occurred. Please try again later.",
    )


# ── Service Functions ──────────────────────────────────────────────────────────

async def create_problem(data: SubmitProblemRequest) -> ProblemReportSchema:
    """
    Insert a new problem + its evidence into Supabase.
    Returns the newly created ProblemReport.
    """
    client = get_supabase_admin_client()
    problem_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    # ── 1. Insert problem row ──────────────────────────────────────────────────
    problem_row = {
        "id": problem_id,
        "title": data.title,
        "description": data.description,
        "category": data.category,
        "subcategory": data.subcategory,
        "urgency": data.urgency,
        "affected_population": data.affected_population,
        "location_lat": data.location.lat,
        "location_lng": data.location.lng,
        "location_name": data.location.name,
        "location_district": data.location.district,
        "reporter_name": data.reporter_name,
        "status": ProblemStatus.SUBMITTED,
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    try:
        res = client.table("problems").insert(problem_row).execute()
    except Exception as exc:
        raise _db_error(exc, "insert problem")

    if not res.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Problem creation failed — no data returned from database.",
        )

    inserted_problem = res.data[0]

    # ── 2. Insert evidence rows ────────────────────────────────────────────────
    inserted_evidence: list[dict] = []
    if data.evidence:
        evidence_rows = [
            {
                "id": str(uuid.uuid4()),
                "problem_id": problem_id,
                "type": ev.type,
                "url": ev.url,
                "name": ev.name,
                "created_at": now_iso,
            }
            for ev in data.evidence
        ]
        try:
            ev_res = client.table("problem_evidence").insert(evidence_rows).execute()
            inserted_evidence = ev_res.data or []
        except Exception as exc:
            # Evidence insert failure is non-fatal for MVP; log and continue
            print(f"[WARN] Evidence insert failed for problem {problem_id}: {exc}")

    return _row_to_problem_report(inserted_problem, inserted_evidence)


async def list_problems(
    category: Optional[str] = None,
    district: Optional[str] = None,
    search: Optional[str] = None,
) -> list[ProblemReportSchema]:
    """
    Fetch all problems with optional server-side filtering.
    Returns newest first.
    """
    client = get_supabase_admin_client()

    try:
        query = (
            client.table("problems")
            .select("*")
            .order("created_at", desc=True)
        )

        # ── Server-side filters ────────────────────────────────────────────────
        if category and category.lower() != "all":
            query = query.eq("category", category)

        if district and district.lower() != "all":
            query = query.eq("location_district", district)

        if search and search.strip():
            # Supabase ilike filter on title (fast); description search via ilike OR
            search_term = f"%{search.strip()}%"
            query = query.or_(f"title.ilike.{search_term},description.ilike.{search_term}")

        res = query.execute()
    except Exception as exc:
        raise _db_error(exc, "list problems")

    if not res.data:
        return []

    problem_ids = [row["id"] for row in res.data]

    # ── Bulk-fetch evidence for all returned problems ──────────────────────────
    evidence_by_problem: dict[str, list[dict]] = {pid: [] for pid in problem_ids}
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
        print(f"[WARN] Could not fetch evidence in list_problems: {exc}")

    return [
        _row_to_problem_report(row, evidence_by_problem.get(row["id"], []))
        for row in res.data
    ]


async def get_problem(problem_id: str) -> ProblemReportSchema:
    """
    Fetch a single problem by UUID, including its evidence.
    Raises HTTP 404 if not found.
    """
    client = get_supabase_admin_client()

    try:
        res = (
            client.table("problems")
            .select("*")
            .eq("id", problem_id)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        raise _db_error(exc, f"get problem {problem_id}")

    if not res.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Problem '{problem_id}' not found.",
        )

    row = res.data[0]

    # Fetch evidence
    try:
        ev_res = (
            client.table("problem_evidence")
            .select("*")
            .eq("problem_id", problem_id)
            .execute()
        )
        evidence = ev_res.data or []
    except Exception as exc:
        print(f"[WARN] Could not fetch evidence for problem {problem_id}: {exc}")
        evidence = []

    return _row_to_problem_report(row, evidence)


async def analyze_problem(
    problem_id: str,
    force_fallback: bool = False,
) -> AIAnalysisSchema:
    """
    Fetch problem by ID, analyze it using AI provider (or fallback),
    update status in Supabase to ANALYZED, and return AIAnalysisSchema.
    Raises 404 if problem does not exist.
    """
    # 1. Fetch problem (raises 404 if not found)
    problem = await get_problem(problem_id)

    # 2. Run AI Analysis
    analysis = await analyze_problem_with_ai(problem, force_fallback=force_fallback)

    # 3. Update status in Supabase to ANALYZED
    client = get_supabase_admin_client()
    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        client.table("problems").update({
            "status": ProblemStatus.ANALYZED,
            "updated_at": now_iso,
        }).eq("id", problem_id).execute()
    except Exception as exc:
        print(f"[WARN] Failed to update status for problem {problem_id} to ANALYZED: {exc}")

    return analysis

