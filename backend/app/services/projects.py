"""
Project service — Stage 4B-A.

Implements:
  - create_project()       → POST /api/projects
  - list_projects()        → GET  /api/projects
  - get_project()          → GET  /api/projects/{project_id}
  - update_project()       → PUT  /api/projects/{project_id}

Uses Supabase Python client. Memory/fallback storage enabled if table is not in database.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status

from app.core.database import get_supabase_admin_client
from app.schemas.enums import ProjectStatus
from app.schemas.projects import (
    CreateProjectRequest,
    ProjectSchema,
    TeamMemberSchema,
    UpdateProjectRequest,
)

# In-memory store fallback if Supabase 'projects' table is not present
_MEMORY_PROJECTS: dict[str, dict] = {}


def _db_error(exc: Exception, context: str) -> HTTPException:
    """Wrap unexpected DB errors into a clean HTTP 500."""
    print(f"[DB ERROR] {context}: {exc}")
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="A database error occurred. Please try again later.",
    )


async def _get_challenge_title(challenge_id: str) -> str:
    """Verify challenge exists and fetch its title; raise 404 if missing."""
    client = get_supabase_admin_client()
    try:
        res = client.table("challenges").select("title").eq("id", challenge_id).limit(1).execute()
        if not res.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Challenge '{challenge_id}' not found.",
            )
        return res.data[0].get("title", "")
    except HTTPException:
        raise
    except Exception as exc:
        raise _db_error(exc, "get_challenge_title")


def _to_project_schema(data: dict) -> ProjectSchema:
    """Helper to convert project dictionary row to ProjectSchema."""
    team_data = data.get("team") or []
    team_members = [
        TeamMemberSchema(
            id=m.get("id", str(uuid.uuid4())),
            name=m.get("name", ""),
            role=m.get("role", ""),
            avatar_url=m.get("avatar_url") or m.get("avatarUrl"),
        )
        if isinstance(m, dict) else m
        for m in team_data
    ]
    return ProjectSchema(
        id=str(data["id"]),
        challenge_id=str(data.get("challenge_id") or data.get("challengeId")),
        challenge_title=data.get("challenge_title") or data.get("challengeTitle") or "",
        title=data.get("title", ""),
        status=ProjectStatus(data.get("status", "PROPOSAL")),
        progress=float(data.get("progress", 0.0)),
        team=team_members,
        faculty_mentor=data.get("faculty_mentor") or data.get("facultyMentor") or "",
        industry_partner=data.get("industry_partner") or data.get("industryPartner") or "",
        created_at=data.get("created_at") or data.get("createdAt") or datetime.now(timezone.utc).isoformat(),
    )


async def create_project(payload: CreateProjectRequest) -> ProjectSchema:
    """
    Create a new project workspace linked to a challenge.

    Rules:
      - Validates challenge_id exists (returns 404 if not found).
      - Initial status = PROPOSAL.
      - Initial progress = 0.
    """
    challenge_title = await _get_challenge_title(payload.challenge_id)
    project_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    project_dict = {
        "id": project_id,
        "challenge_id": payload.challenge_id,
        "challenge_title": challenge_title,
        "title": payload.title,
        "description": payload.description or "",
        "status": ProjectStatus.PROPOSAL.value,
        "progress": 0.0,
        "team": [m.model_dump(by_alias=False) for m in payload.team],
        "faculty_mentor": payload.faculty_mentor,
        "industry_partner": payload.industry_partner,
        "created_at": now_iso,
    }

    client = get_supabase_admin_client()
    try:
        res = client.table("projects").insert(project_dict).execute()
        if res.data:
            return _to_project_schema(res.data[0])
    except Exception as exc:
        print(f"[PROJECT SERVICE] Supabase insert fallback to memory: {exc}")

    _MEMORY_PROJECTS[project_id] = project_dict
    return _to_project_schema(project_dict)


async def list_projects() -> list[ProjectSchema]:
    """Return all project workspaces."""
    client = get_supabase_admin_client()
    try:
        res = client.table("projects").select("*").order("created_at", desc=True).execute()
        if res.data:
            db_projects = [_to_project_schema(row) for row in res.data]
            mem_projects = [_to_project_schema(p) for p in _MEMORY_PROJECTS.values() if p["id"] not in [r["id"] for r in res.data]]
            return db_projects + mem_projects
    except Exception as exc:
        print(f"[PROJECT SERVICE] Supabase select list fallback to memory: {exc}")

    return [_to_project_schema(p) for p in _MEMORY_PROJECTS.values()]


async def get_project(project_id: str) -> ProjectSchema:
    """Fetch project details by ID; raise 404 if not found."""
    client = get_supabase_admin_client()
    try:
        res = client.table("projects").select("*").eq("id", project_id).limit(1).execute()
        if res.data:
            return _to_project_schema(res.data[0])
    except Exception as exc:
        print(f"[PROJECT SERVICE] Supabase get by ID fallback to memory: {exc}")

    if project_id in _MEMORY_PROJECTS:
        return _to_project_schema(_MEMORY_PROJECTS[project_id])

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Project '{project_id}' not found.",
    )


async def update_project(project_id: str, payload: UpdateProjectRequest) -> ProjectSchema:
    """
    Update project details, status, or progress.
    Returns 404 if project does not exist.
    """
    existing = await get_project(project_id)

    updates = {}
    if payload.title is not None:
        updates["title"] = payload.title
    if payload.description is not None:
        updates["description"] = payload.description
    if payload.status is not None:
        updates["status"] = payload.status.value if hasattr(payload.status, "value") else str(payload.status)
    if payload.progress is not None:
        updates["progress"] = payload.progress
    if payload.team is not None:
        updates["team"] = [m.model_dump(by_alias=False) for m in payload.team]
    if payload.faculty_mentor is not None:
        updates["faculty_mentor"] = payload.faculty_mentor
    if payload.industry_partner is not None:
        updates["industry_partner"] = payload.industry_partner

    if not updates:
        return existing

    client = get_supabase_admin_client()
    try:
        res = client.table("projects").update(updates).eq("id", project_id).execute()
        if res.data:
            return _to_project_schema(res.data[0])
    except Exception as exc:
        print(f"[PROJECT SERVICE] Supabase update fallback to memory: {exc}")

    if project_id in _MEMORY_PROJECTS:
        current = _MEMORY_PROJECTS[project_id]
        current.update(updates)
        return _to_project_schema(current)

    # In case it came from DB initially but update fallback triggered
    current_dict = {
        "id": existing.id,
        "challenge_id": existing.challenge_id,
        "challenge_title": existing.challenge_title,
        "title": existing.title,
        "status": existing.status.value,
        "progress": existing.progress,
        "team": [m.model_dump(by_alias=False) if hasattr(m, "model_dump") else m for m in existing.team],
        "faculty_mentor": existing.faculty_mentor,
        "industry_partner": existing.industry_partner,
        "created_at": existing.created_at,
    }
    current_dict.update(updates)
    _MEMORY_PROJECTS[project_id] = current_dict
    return _to_project_schema(current_dict)
