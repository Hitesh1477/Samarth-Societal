"""
Stage 5A test suite — run from backend/ directory:
    python -u test_stage5a.py

Covers:
  1. Route registration (POST /api/projects/{id}/milestones, PUT /api/milestones/{id})
  2. Nonexistent project reference -> 404
  3. Milestone creation linked to a project -> 201
  4. Nonexistent milestone update -> 404
  5. GET/PUT milestone update -> 200
  6. Progress validation (progress outside 0-100 -> 422)
  7. Status validation (invalid milestone status enum -> 422)
  8. Automatic project progress calculation update
  9. CamelCase response validation (dueDate, evidenceCount)
  10. Isolated test data cleanup
"""

import json
import urllib.request
import urllib.error
import uuid
from typing import Any

from app.core.database import get_supabase_admin_client

BASE = "http://localhost:8000"


def request(method: str, path: str, body: dict | None = None) -> tuple[int, Any]:
    """Execute HTTP request to local backend dev server."""
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            try:
                return r.status, json.loads(raw)
            except json.JSONDecodeError:
                return r.status, raw.decode(errors="replace")
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw.decode(errors="replace")
    except Exception as exc:
        return 0, f"CONNECTION ERROR: {exc}"


_results: list[bool] = []


def check(label: str, condition: bool, detail: str = "") -> bool:
    """Record test assertion result."""
    tag = "PASS" if condition else "FAIL"
    suffix = f"  ->  {detail}" if detail else ""
    print(f"  [{tag}] {label}{suffix}")
    _results.append(condition)
    return condition


print("\n=== Stage 5A Test Suite: Milestones & Project Progress Backend ===\n")

# ── 1. Route Registration ──────────────────────────────────────────────────────

print("[1] GET /openapi.json  (route registration)")
code, body = request("GET", "/openapi.json")
paths = body.get("paths", {}) if isinstance(body, dict) else {}

check("OpenAPI reachable", code == 200, str(code))
check(
    "POST /api/projects/{project_id}/milestones registered",
    "/api/projects/{project_id}/milestones" in paths
    and "post" in paths.get("/api/projects/{project_id}/milestones", {}),
)
check(
    "PUT /api/milestones/{milestone_id} registered",
    "/api/milestones/{milestone_id}" in paths
    and "put" in paths.get("/api/milestones/{milestone_id}", {}),
)

# ── Test Setup ─────────────────────────────────────────────────────────────────

client = get_supabase_admin_client()
test_challenge_id = str(uuid.uuid4())
test_project_id: str | None = None
test_milestone_id_1: str | None = None
test_milestone_id_2: str | None = None

try:
    # Insert test challenge into DB
    chal_row = {
        "id": test_challenge_id,
        "title": "Stage 5A Challenge: River Water Quality Monitoring",
        "category": "Environment",
        "subcategory": "Water Quality",
        "priority": 90,
        "priority_level": "HIGH",
        "status": "NEW",
        "affected_population": 12000,
        "report_count": 5,
        "district": "Kamrup",
        "location_name": "Brahmaputra Bank",
        "lat": 26.1839,
        "lng": 91.7401,
    }
    client.table("challenges").insert(chal_row).execute()

    # Create project via POST /api/projects
    p_req = {
        "challengeId": test_challenge_id,
        "title": "Water Quality Sensor Array Deployment",
    }
    code, p_res = request("POST", "/api/projects", p_req)
    if isinstance(p_res, dict):
        test_project_id = p_res.get("id")

    check("Test project initialized", bool(test_project_id), str(test_project_id))

    # ── 2. Invalid Project Milestone Creation (404) ─────────────────────────────

    print("\n[2] POST /api/projects/00000000-0000-0000-0000-000000000000/milestones (expect 404)")
    code, res = request(
        "POST",
        "/api/projects/00000000-0000-0000-0000-000000000000/milestones",
        {"title": "Orphan Milestone"},
    )
    check("HTTP 404 for invalid project_id", code == 404, str(code))

    # ── 3. Valid Milestone Creation ─────────────────────────────────────────────

    if test_project_id:
        print(f"\n[3] POST /api/projects/{test_project_id}/milestones (create milestone 1)")
        m1_req = {
            "title": "Milestone 1: Sensor Procurement & Calibration",
            "status": "in_progress",
            "progress": 50.0,
            "dueDate": "2026-10-15",
            "evidenceCount": 2,
        }
        code, res = request("POST", f"/api/projects/{test_project_id}/milestones", m1_req)
        check("HTTP 201 Created", code == 201, str(code))
        check("Response is dict", isinstance(res, dict), type(res).__name__)
        if isinstance(res, dict):
            test_milestone_id_1 = res.get("id")
            check("Has milestone id", bool(test_milestone_id_1), str(test_milestone_id_1))
            check("Title matches", res.get("title") == m1_req["title"], str(res.get("title")))
            check("Status matches", res.get("status") == "in_progress", str(res.get("status")))
            check("Progress matches", res.get("progress") == 50.0, str(res.get("progress")))
            check("DueDate matches", res.get("dueDate") == "2026-10-15", str(res.get("dueDate")))
            check("EvidenceCount matches", res.get("evidenceCount") == 2, str(res.get("evidenceCount")))

    # ── 4. Project Progress Auto-Update (Single Milestone) ─────────────────────

    if test_project_id:
        print(f"\n[4] GET /api/projects/{test_project_id} (verify project progress auto-update)")
        code, res = request("GET", f"/api/projects/{test_project_id}")
        check("HTTP 200 OK", code == 200, str(code))
        if isinstance(res, dict):
            check("Project progress updated to milestone 1 progress (50.0)", res.get("progress") == 50.0, str(res.get("progress")))

    # ── 5. Second Milestone & Average Calculation ───────────────────────────────

    if test_project_id:
        print(f"\n[5] POST /api/projects/{test_project_id}/milestones (create milestone 2)")
        m2_req = {
            "title": "Milestone 2: Field Installation at Site A",
            "status": "pending",
            "progress": 10.0,
            "dueDate": "2026-11-30",
            "evidenceCount": 0,
        }
        code, res = request("POST", f"/api/projects/{test_project_id}/milestones", m2_req)
        check("HTTP 201 Created", code == 201, str(code))
        if isinstance(res, dict):
            test_milestone_id_2 = res.get("id")

        print(f"    Checking recalculated project average progress ((50 + 10) / 2 = 30.0)...")
        code, res = request("GET", f"/api/projects/{test_project_id}")
        if isinstance(res, dict):
            check("Project progress recalculated to average (30.0)", res.get("progress") == 30.0, str(res.get("progress")))

    # ── 6. Nonexistent Milestone PUT (404) ──────────────────────────────────────

    print("\n[6] PUT /api/milestones/00000000-0000-0000-0000-000000000000 (expect 404)")
    code, res = request(
        "PUT",
        "/api/milestones/00000000-0000-0000-0000-000000000000",
        {"title": "Ghost Milestone"},
    )
    check("HTTP 404 for nonexistent milestone", code == 404, str(code))

    # ── 7. PUT Update Milestone ─────────────────────────────────────────────────

    if test_milestone_id_1 and test_project_id:
        print(f"\n[7] PUT /api/milestones/{test_milestone_id_1} (complete milestone 1)")
        u_req = {
            "status": "completed",
            "progress": 100.0,
            "evidenceCount": 4,
        }
        code, res = request("PUT", f"/api/milestones/{test_milestone_id_1}", u_req)
        check("HTTP 200 OK", code == 200, str(code))
        if isinstance(res, dict):
            check("Milestone 1 status updated to completed", res.get("status") == "completed", str(res.get("status")))
            check("Milestone 1 progress updated to 100.0", res.get("progress") == 100.0, str(res.get("progress")))

        print(f"    Checking project progress after milestone 1 completion ((100 + 10) / 2 = 55.0)...")
        code, res = request("GET", f"/api/projects/{test_project_id}")
        if isinstance(res, dict):
            check("Project progress updated to 55.0", res.get("progress") == 55.0, str(res.get("progress")))

    # ── 8. Progress Validation (422) ────────────────────────────────────────────

    if test_milestone_id_1:
        print(f"\n[8] PUT /api/milestones/{test_milestone_id_1} with invalid progress (>100)")
        code, res = request("PUT", f"/api/milestones/{test_milestone_id_1}", {"progress": 120.0})
        check("HTTP 422 for progress > 100", code == 422, str(code))

        code, res = request("PUT", f"/api/milestones/{test_milestone_id_1}", {"progress": -5.0})
        check("HTTP 422 for progress < 0", code == 422, str(code))

    # ── 9. Status Enum Validation (422) ─────────────────────────────────────────

    if test_milestone_id_1:
        print(f"\n[9] PUT /api/milestones/{test_milestone_id_1} with invalid status enum")
        code, res = request("PUT", f"/api/milestones/{test_milestone_id_1}", {"status": "INVALID_STATUS"})
        check("HTTP 422 for invalid status enum", code == 422, str(code))

    # ── 10. CamelCase Field Validation ─────────────────────────────────────────

    if test_milestone_id_1:
        print("\n[10] CamelCase response field validation")
        code, res = request("PUT", f"/api/milestones/{test_milestone_id_1}", {"evidenceCount": 5})
        check("HTTP 200 OK", code == 200, str(code))
        if isinstance(res, dict):
            required_camel = ["id", "title", "status", "progress", "dueDate", "evidenceCount"]
            missing = [f for f in required_camel if f not in res]
            check("All required camelCase fields present", len(missing) == 0, f"missing={missing}")

            snake_keys = ["due_date", "evidence_count", "project_id"]
            leaked = [f for f in snake_keys if f in res]
            check("No snake_case fields leaked into response", len(leaked) == 0, f"leaked={leaked}")

finally:
    # ── Cleanup ─────────────────────────────────────────────────────────────────
    print("\n[CLEANUP] Removing isolated test records...")
    if test_milestone_id_1:
        try:
            client.table("milestones").delete().eq("id", test_milestone_id_1).execute()
            print(f"  -> Deleted test milestone 1: {test_milestone_id_1}")
        except Exception:
            pass
    if test_milestone_id_2:
        try:
            client.table("milestones").delete().eq("id", test_milestone_id_2).execute()
            print(f"  -> Deleted test milestone 2: {test_milestone_id_2}")
        except Exception:
            pass
    if test_project_id:
        try:
            client.table("projects").delete().eq("id", test_project_id).execute()
            print(f"  -> Deleted test project: {test_project_id}")
        except Exception:
            pass
    try:
        client.table("challenges").delete().eq("id", test_challenge_id).execute()
        print(f"  -> Deleted test challenge: {test_challenge_id}")
    except Exception:
        pass
    print("  -> Cleanup complete.")

passed = sum(1 for r in _results if r)
total = len(_results)
print(f"\n==================================================")
print(f"Results: {passed}/{total} assertions passed")
print(f"==================================================\n")
