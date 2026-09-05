"""
Stage 4B test suite — run from backend/ directory:
    python -u test_stage4b.py

Covers:
  1. Route registration (POST/GET/PUT /api/projects)
  2. Nonexistent challenge reference -> 404
  3. Project creation linked to a challenge -> 201
  4. Initial project state (status=PROPOSAL, progress=0, team, etc.)
  5. GET project list -> 200
  6. GET project by ID -> 200
  7. Nonexistent project ID -> 404
  8. PUT project update (title, description, status, progress, team, facultyMentor, industryPartner)
  9. Progress validation (progress outside 0-100 -> 422)
  10. Status validation (invalid enum status -> 422)
  11. CamelCase field validation (no snake_case leakage)
  12. Isolated test data cleanup
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


print("\n=== Stage 4B Test Suite: Solution/Project Workspace Backend ===\n")

# ── 1. Route Registration ──────────────────────────────────────────────────────

print("[1] GET /openapi.json  (route registration)")
code, body = request("GET", "/openapi.json")
paths = body.get("paths", {}) if isinstance(body, dict) else {}

check("OpenAPI reachable", code == 200, str(code))
check("POST /api/projects registered", "/api/projects" in paths and "post" in paths.get("/api/projects", {}))
check("GET  /api/projects registered", "/api/projects" in paths and "get" in paths.get("/api/projects", {}))
check("GET  /api/projects/{project_id} registered", "/api/projects/{project_id}" in paths and "get" in paths.get("/api/projects/{project_id}", {}))
check("PUT  /api/projects/{project_id} registered", "/api/projects/{project_id}" in paths and "put" in paths.get("/api/projects/{project_id}", {}))

# ── Test Setup ─────────────────────────────────────────────────────────────────

client = get_supabase_admin_client()
test_challenge_id = str(uuid.uuid4())
test_project_id: str | None = None

try:
    # Insert test challenge into DB to establish foreign key requirement
    chal_row = {
        "id": test_challenge_id,
        "title": "Stage 4B Test Challenge: Urban Drainage Overhaul",
        "description": "Challenge for testing project workspace creation.",
        "category": "Infrastructure",
        "subcategory": "Drainage",
        "priority": 85,
        "priority_level": "HIGH",
        "status": "NEW",
        "affected_population": 5000,
        "report_count": 3,
        "district": "Kamrup Metropolitan",
        "location_name": "Ganeshguri",
        "lat": 26.1445,
        "lng": 91.7362,
    }
    client.table("challenges").insert(chal_row).execute()

    # ── 2. Invalid Challenge Reference ──────────────────────────────────────────

    print("\n[2] POST /api/projects with invalid challenge_id (expect 404)")
    invalid_chal_id = str(uuid.uuid4())
    bad_payload = {
        "challengeId": invalid_chal_id,
        "title": "Invalid Challenge Project",
    }
    code, res = request("POST", "/api/projects", bad_payload)
    check("HTTP 404 for invalid challenge_id", code == 404, str(code))

    # ── 3. Project Creation ────────────────────────────────────────────────────

    print("\n[3] POST /api/projects (valid project creation)")
    create_payload = {
        "challengeId": test_challenge_id,
        "title": "Smart Drainage Solution Project",
        "description": "AI-guided automated flood detection and drainage system.",
        "team": [
            {"id": str(uuid.uuid4()), "name": "Dr. Rahul Sharma", "role": "Lead Researcher"},
            {"id": str(uuid.uuid4()), "name": "Priya Patel", "role": "Software Lead"},
        ],
        "facultyMentor": "Prof. A. K. Singh",
        "industryPartner": "TechSolutions Pvt Ltd",
    }
    code, res = request("POST", "/api/projects", create_payload)
    check("HTTP 201 Created", code == 201, str(code))
    check("Response is dict", isinstance(res, dict), type(res).__name__)
    if isinstance(res, dict):
        test_project_id = res.get("id")
        check("Has project id", bool(test_project_id), str(test_project_id))
        check("Linked to correct challengeId", res.get("challengeId") == test_challenge_id, str(res.get("challengeId")))
        check("Challenge title populated", res.get("challengeTitle") == chal_row["title"], str(res.get("challengeTitle")))
        check("Initial status is PROPOSAL", res.get("status") == "PROPOSAL", str(res.get("status")))
        check("Initial progress is 0", res.get("progress") == 0, str(res.get("progress")))
        check("Team size matches", len(res.get("team", [])) == 2, str(len(res.get("team", []))))
        check("Faculty mentor matches", res.get("facultyMentor") == create_payload["facultyMentor"], str(res.get("facultyMentor")))
        check("Industry partner matches", res.get("industryPartner") == create_payload["industryPartner"], str(res.get("industryPartner")))

    # ── 4. GET Projects List ────────────────────────────────────────────────────

    print("\n[4] GET /api/projects (list projects)")
    code, res = request("GET", "/api/projects")
    check("HTTP 200 OK", code == 200, str(code))
    check("Response is list", isinstance(res, list), type(res).__name__)
    if isinstance(res, list) and test_project_id:
        p_ids = [p.get("id") for p in res if isinstance(p, dict)]
        check("Created project present in list", test_project_id in p_ids, f"found {len(p_ids)} projects")

    # ── 5. GET Project by ID ────────────────────────────────────────────────────

    if test_project_id:
        print(f"\n[5] GET /api/projects/{test_project_id}")
        code, res = request("GET", f"/api/projects/{test_project_id}")
        check("HTTP 200 OK", code == 200, str(code))
        check("Response matches created ID", res.get("id") == test_project_id, str(res.get("id")))

    # ── 6. Nonexistent Project GET (404) ────────────────────────────────────────

    print("\n[6] GET /api/projects/00000000-0000-0000-0000-000000000000 (expect 404)")
    code, res = request("GET", "/api/projects/00000000-0000-0000-0000-000000000000")
    check("HTTP 404 for nonexistent project", code == 404, str(code))

    # ── 7. PUT Update Project ───────────────────────────────────────────────────

    if test_project_id:
        print(f"\n[7] PUT /api/projects/{test_project_id} (update workspace)")
        update_payload = {
            "title": "Smart Drainage Solution Project (Phase 1)",
            "description": "Updated project description with sensor details.",
            "status": "ACTIVE",
            "progress": 35.5,
            "facultyMentor": "Prof. A. K. Singh & Dr. Verma",
            "industryPartner": "TechSolutions & SmartGov",
            "team": [
                {"id": str(uuid.uuid4()), "name": "Dr. Rahul Sharma", "role": "Principal Investigator"},
                {"id": str(uuid.uuid4()), "name": "Priya Patel", "role": "Software Lead"},
                {"id": str(uuid.uuid4()), "name": "Amit Kumar", "role": "Hardware Engineer"},
            ],
        }
        code, res = request("PUT", f"/api/projects/{test_project_id}", update_payload)
        check("HTTP 200 OK", code == 200, str(code))
        if isinstance(res, dict):
            check("Updated title", res.get("title") == update_payload["title"], str(res.get("title")))
            check("Updated status", res.get("status") == "ACTIVE", str(res.get("status")))
            check("Updated progress", res.get("progress") == 35.5, str(res.get("progress")))
            check("Updated team size", len(res.get("team", [])) == 3, str(len(res.get("team", []))))
            check("Updated faculty mentor", res.get("facultyMentor") == update_payload["facultyMentor"], str(res.get("facultyMentor")))

    # ── 8. Progress Validation (422) ────────────────────────────────────────────

    if test_project_id:
        print(f"\n[8] PUT /api/projects/{test_project_id} with invalid progress (>100)")
        code, res = request("PUT", f"/api/projects/{test_project_id}", {"progress": 150.0})
        check("HTTP 422 for progress > 100", code == 422, str(code))

        code, res = request("PUT", f"/api/projects/{test_project_id}", {"progress": -10.0})
        check("HTTP 422 for progress < 0", code == 422, str(code))

    # ── 9. Status Validation (422) ──────────────────────────────────────────────

    if test_project_id:
        print(f"\n[9] PUT /api/projects/{test_project_id} with invalid status enum")
        code, res = request("PUT", f"/api/projects/{test_project_id}", {"status": "INVALID_STATUS"})
        check("HTTP 422 for invalid status enum", code == 422, str(code))

    # ── 10. CamelCase Field Validation ─────────────────────────────────────────

    if test_project_id:
        print("\n[10] CamelCase response field validation")
        code, res = request("GET", f"/api/projects/{test_project_id}")
        required_camel = [
            "id",
            "challengeId",
            "challengeTitle",
            "title",
            "status",
            "progress",
            "team",
            "facultyMentor",
            "industryPartner",
            "createdAt",
        ]
        missing = [f for f in required_camel if f not in res]
        check("All required camelCase fields present", len(missing) == 0, f"missing={missing}")

        snake_keys = ["challenge_id", "challenge_title", "faculty_mentor", "industry_partner", "created_at"]
        leaked = [f for f in snake_keys if f in res]
        check("No snake_case fields leaked into response", len(leaked) == 0, f"leaked={leaked}")

finally:
    # ── Cleanup ─────────────────────────────────────────────────────────────────
    print("\n[CLEANUP] Removing isolated test records...")
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
