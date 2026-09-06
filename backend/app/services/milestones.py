"""
Milestone service — Stage 5A.

Implements:
  - create_milestone()   → POST /api/projects/{project_id}/milestones
  - update_milestone()   → PUT  /api/milestones/{milestone_id}
  - list_project_milestones() -> internal helper to list milestones for a project

Calculates and updates parent project progress automatically when milestones change.
Uses Supabase Python client with an in-memory store fallback.
"""

import uuid
from typing import Optional

from fastapi import HTTPException, status

from app.core.database import get_supabase_admin_client
from app.schemas.enums import MilestoneStatus
from app.schemas.milestones import (
    CreateMilestoneRequest,
    MilestoneSchema,
    UpdateMilestoneRequest,
)
from app.schemas.projects import UpdateProjectRequest
from app.services import projects as project_service

# In-memory store fallback if Supabase 'milestones' table is missing
_MEMORY_MILESTONES: dict[str, dict] = {}


def _to_milestone_schema(data: dict) -> MilestoneSchema:
    """Helper to convert dictionary row → MilestoneSchema."""
    raw_status = data.get("status", "pending")
    if hasattr(raw_status, "value"):
        raw_status = raw_status.value

    return MilestoneSchema(
        id=str(data["id"]),
        title=str(data.get("title", "")),
        status=MilestoneStatus(str(raw_status)),
        progress=float(data.get("progress", 0.0)),
        due_date=str(data.get("due_date") or data.get("dueDate") or ""),
        evidence_count=int(data.get("evidence_count") or data.get("evidenceCount") or 0),
    )


async def _recalculate_project_progress(project_id: str) -> None:
    """
    Calculate simple average progress of all milestones for a project
    and update parent project progress automatically.
    """
    milestones = await list_project_milestones(project_id)
    if not milestones:
        return

    total_progress = sum(m.progress for m in milestones)
    avg_progress = round(total_progress / len(milestones), 1)

    try:
        await project_service.update_project(
            project_id, UpdateProjectRequest(progress=avg_progress)
        )
    except Exception as exc:
        print(f"[MILESTONE SERVICE] Failed to update project progress: {exc}")


async def list_project_milestones(project_id: str) -> list[MilestoneSchema]:
    """Internal helper: fetch all milestones for a project."""
    client = get_supabase_admin_client()
    try:
        res = client.table("milestones").select("*").eq("project_id", project_id).execute()
        db_ms = [_to_milestone_schema(row) for row in (res.data or [])]
        if res.data is not None:
            return db_ms
    except Exception as exc:
        print(f"[MILESTONE SERVICE] Supabase query fallback to memory: {exc}")

    return [
        _to_milestone_schema(m)
        for m in _MEMORY_MILESTONES.values()
        if m.get("project_id") == project_id
    ]


async def list_project_milestones_for_api(project_id: str) -> list[MilestoneSchema]:
    """Verify the project exists, then return its persisted milestones."""
    await project_service.get_project(project_id)
    return await list_project_milestones(project_id)


async def create_milestone(project_id: str, payload: CreateMilestoneRequest) -> MilestoneSchema:
    """
    Create a milestone for an existing project.
    Validates project existence (returns HTTP 404 if project not found).
    Recalculates parent project progress automatically.
    """
    # Verify project exists first
    project = await project_service.get_project(project_id)

    milestone_id = str(uuid.uuid4())
    st_val = payload.status.value if hasattr(payload.status, "value") else str(payload.status or "pending")

    m_dict = {
        "id": milestone_id,
        "project_id": project.id,
        "title": payload.title,
        "status": st_val,
        "progress": payload.progress or 0.0,
        "due_date": payload.due_date or "",
        "evidence_count": payload.evidence_count or 0,
    }

    client = get_supabase_admin_client()
    try:
        res = client.table("milestones").insert(m_dict).execute()
        if res.data:
            created = _to_milestone_schema(res.data[0])
            await _recalculate_project_progress(project.id)
            return created
    except Exception as exc:
        print(f"[MILESTONE SERVICE] Supabase insert fallback to memory: {exc}")

    _MEMORY_MILESTONES[milestone_id] = m_dict
    created = _to_milestone_schema(m_dict)
    await _recalculate_project_progress(project.id)
    return created


async def update_milestone(milestone_id: str, payload: UpdateMilestoneRequest) -> MilestoneSchema:
    """
    Update milestone fields.
    Returns HTTP 404 if milestone is not found.
    Recalculates parent project progress automatically.
    """
    existing_dict: Optional[dict] = None
    project_id: Optional[str] = None

    client = get_supabase_admin_client()
    try:
        res = client.table("milestones").select("*").eq("id", milestone_id).limit(1).execute()
        if res.data:
            existing_dict = res.data[0]
            project_id = str(existing_dict.get("project_id"))
    except Exception as exc:
        print(f"[MILESTONE SERVICE] Supabase select fallback to memory: {exc}")

    if not existing_dict and milestone_id in _MEMORY_MILESTONES:
        existing_dict = _MEMORY_MILESTONES[milestone_id]
        project_id = str(existing_dict.get("project_id"))

    if not existing_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Milestone '{milestone_id}' not found.",
        )

    updates = {}
    if payload.title is not None:
        updates["title"] = payload.title
    if payload.status is not None:
        updates["status"] = payload.status.value if hasattr(payload.status, "value") else str(payload.status)
    if payload.progress is not None:
        updates["progress"] = payload.progress
    if payload.due_date is not None:
        updates["due_date"] = payload.due_date
    if payload.evidence_count is not None:
        updates["evidence_count"] = payload.evidence_count

    if updates:
        try:
            res = client.table("milestones").update(updates).eq("id", milestone_id).execute()
            if res.data:
                updated = _to_milestone_schema(res.data[0])
                if project_id:
                    await _recalculate_project_progress(project_id)
                return updated
        except Exception as exc:
            print(f"[MILESTONE SERVICE] Supabase update fallback to memory: {exc}")

        existing_dict.update(updates)
        _MEMORY_MILESTONES[milestone_id] = existing_dict

    updated = _to_milestone_schema(existing_dict)
    if project_id:
        await _recalculate_project_progress(project_id)
    return updated
