"""
Stage 5B test suite — run from backend/ directory:
    python -u test_stage5b.py

Covers:
  PART A: Pilot Tracking
    1. Route registration (POST/PUT /api/challenges/{id}/pilot)
    2. Nonexistent challenge pilot creation -> 404
    3. Valid pilot creation (planned, active, completed)
    4. Invalid pilot status -> 422
    5. Negative participants validation -> 422
    6. Pilot update (PUT)

  PART B & C: Impact Metrics Tracking & Validation
    7. Route registration (POST/GET /api/projects/{id}/impact)
    8. Nonexistent project impact GET -> 404
    9. Nonexistent project impact metric creation -> 404
    10. GET impact for project with NO metrics -> returns valid pending response (impactScore=0, metrics=[])
    11. Impact metric creation (POST)
    12. Deterministic improvement percentage calculation
    13. Deterministic impactScore calculation
    14. Empty metric label validation -> 422
    15. CamelCase response field validation (projectId, impactScore, beforeImage, afterImage)
    16. Isolated test data cleanup
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


print("\n=== Stage 5B Test Suite: Pilot & Impact Tracking Backend ===\n")

# ── 1. Route Registration ──────────────────────────────────────────────────────

print("[1] GET /openapi.json  (route registration)")
code, body = request("GET", "/openapi.json")
paths = body.get("paths", {}) if isinstance(body, dict) else {}

check("OpenAPI reachable", code == 200, str(code))
check(
    "POST /api/challenges/{challenge_id}/pilot registered",
    "/api/challenges/{challenge_id}/pilot" in paths
    and "post" in paths.get("/api/challenges/{challenge_id}/pilot", {}),
)
check(
    "PUT  /api/challenges/{challenge_id}/pilot registered",
    "/api/challenges/{challenge_id}/pilot" in paths
    and "put" in paths.get("/api/challenges/{challenge_id}/pilot", {}),
)
check(
    "POST /api/projects/{project_id}/impact registered",
    "/api/projects/{project_id}/impact" in paths
    and "post" in paths.get("/api/projects/{project_id}/impact", {}),
)
check(
    "GET  /api/projects/{project_id}/impact registered",
    "/api/projects/{project_id}/impact" in paths
    and "get" in paths.get("/api/projects/{project_id}/impact", {}),
)

# ── Test Data Setup ────────────────────────────────────────────────────────────

client = get_supabase_admin_client()
test_challenge_id = str(uuid.uuid4())
test_project_id: str | None = None

try:
    # Insert test challenge into DB
    chal_row = {
        "id": test_challenge_id,
        "title": "Stage 5B Challenge: Urban Solar Microgrid Implementation",
        "category": "Environment",
        "subcategory": "Renewable Energy",
        "priority": 88,
        "priority_level": "HIGH",
        "status": "NEW",
        "affected_population": 8000,
        "report_count": 4,
        "district": "Guwahati",
        "location_name": "Dispur Ward 4",
        "lat": 26.1433,
        "lng": 91.7898,
    }
    client.table("challenges").insert(chal_row).execute()

    # Create project via POST /api/projects
    p_req = {
        "challengeId": test_challenge_id,
        "title": "Rooftop Solar Array Project",
    }
    code, p_res = request("POST", "/api/projects", p_req)
    if isinstance(p_res, dict):
        test_project_id = p_res.get("id")

    check("Test project initialized", bool(test_project_id), str(test_project_id))

    # ── PART A: PILOT TESTS ────────────────────────────────────────────────────

    print("\n[2] POST /api/challenges/00000000-0000-0000-0000-000000000000/pilot (expect 404)")
    code, res = request(
        "POST",
        "/api/challenges/00000000-0000-0000-0000-000000000000/pilot",
        {"startDate": "2026-10-01", "location": "Dispur"},
    )
    check("HTTP 404 for invalid challenge_id", code == 404, str(code))

    print(f"\n[3] POST /api/challenges/{test_challenge_id}/pilot (create pilot)")
    pilot_req = {
        "status": "planned",
        "startDate": "2026-10-01",
        "endDate": "2027-01-31",
        "location": "Dispur Ward 4 Community Center",
        "participants": 250,
    }
    code, res = request("POST", f"/api/challenges/{test_challenge_id}/pilot", pilot_req)
    check("HTTP 201 Created", code == 201, str(code))
    check("Response is dict", isinstance(res, dict), type(res).__name__)
    if isinstance(res, dict):
        check("ChallengeId matches", res.get("challengeId") == test_challenge_id, str(res.get("challengeId")))
        check("Status is planned", res.get("status") == "planned", str(res.get("status")))
        check("StartDate matches", res.get("startDate") == "2026-10-01", str(res.get("startDate")))
        check("EndDate matches", res.get("endDate") == "2027-01-31", str(res.get("endDate")))
        check("Location matches", res.get("location") == pilot_req["location"], str(res.get("location")))
        check("Participants count matches", res.get("participants") == 250, str(res.get("participants")))

    print(f"\n[4] PUT /api/challenges/{test_challenge_id}/pilot (update pilot to active)")
    up_pilot_req = {
        "status": "active",
        "startDate": "2026-10-01",
        "location": "Dispur Ward 4 & Ward 5",
        "participants": 400,
    }
    code, res = request("PUT", f"/api/challenges/{test_challenge_id}/pilot", up_pilot_req)
    check("HTTP 200 OK", code == 200, str(code))
    if isinstance(res, dict):
        check("Status updated to active", res.get("status") == "active", str(res.get("status")))
        check("Participants updated to 400", res.get("participants") == 400, str(res.get("participants")))

    print(f"\n[5] POST /api/challenges/{test_challenge_id}/pilot with negative participants (expect 422)")
    code, res = request("POST", f"/api/challenges/{test_challenge_id}/pilot", {"startDate": "2026-10-01", "location": "Site", "participants": -10})
    check("HTTP 422 for negative participants", code == 422, str(code))

    print(f"\n[6] POST /api/challenges/{test_challenge_id}/pilot with invalid status (expect 422)")
    code, res = request("POST", f"/api/challenges/{test_challenge_id}/pilot", {"startDate": "2026-10-01", "location": "Site", "status": "INVALID_STATUS"})
    check("HTTP 422 for invalid pilot status", code == 422, str(code))

    # ── PART B & C: IMPACT METRICS TESTS ─────────────────────────────────────

    print("\n[7] GET /api/projects/00000000-0000-0000-0000-000000000000/impact (expect 404)")
    code, res = request("GET", "/api/projects/00000000-0000-0000-0000-000000000000/impact")
    check("HTTP 404 for invalid project_id GET", code == 404, str(code))

    print("\n[8] POST /api/projects/00000000-0000-0000-0000-000000000000/impact (expect 404)")
    code, res = request("POST", "/api/projects/00000000-0000-0000-0000-000000000000/impact", {"label": "Test Metric", "before": 10, "after": 20})
    check("HTTP 404 for invalid project_id POST", code == 404, str(code))

    if test_project_id:
        print(f"\n[9] GET /api/projects/{test_project_id}/impact (empty metrics check)")
        code, res = request("GET", f"/api/projects/{test_project_id}/impact")
        check("HTTP 200 OK for empty impact", code == 200, str(code))
        if isinstance(res, dict):
            check("ProjectId matches", res.get("projectId") == test_project_id, str(res.get("projectId")))
            check("ImpactScore is 0 for no metrics", res.get("impactScore") == 0.0, str(res.get("impactScore")))
            check("Status is pending for no metrics", res.get("status") == "pending", str(res.get("status")))
            check("Metrics is an empty list", isinstance(res.get("metrics"), list) and len(res.get("metrics")) == 0, str(res.get("metrics")))

    if test_project_id:
        print(f"\n[10] POST /api/projects/{test_project_id}/impact (add metric 1)")
        m1_req = {
            "label": "Daily Grid Outage Duration",
            "before": 4.5,
            "after": 0.5,
            "unit": "hours/day",
            "summary": "Solar array reduced outages significantly.",
        }
        code, res = request("POST", f"/api/projects/{test_project_id}/impact", m1_req)
        check("HTTP 201 Created", code == 201, str(code))
        if isinstance(res, dict):
            check("Status updated to measured", res.get("status") == "measured", str(res.get("status")))
            metrics = res.get("metrics", [])
            check("Has 1 metric", len(metrics) == 1, str(len(metrics)))
            if len(metrics) == 1:
                m1 = metrics[0]
                check("Label matches", m1.get("label") == m1_req["label"], str(m1.get("label")))
                check("Before matches", m1.get("before") == 4.5, str(m1.get("before")))
                check("After matches", m1.get("after") == 0.5, str(m1.get("after")))
                check("Unit matches", m1.get("unit") == "hours/day", str(m1.get("unit")))
                # improvement = ((0.5 - 4.5) / 4.5) * 100 = -88.9%
                check("Improvement percentage calculated (-88.9%)", m1.get("improvement") == -88.9, str(m1.get("improvement")))
                check("ImpactScore calculated (88.9)", res.get("impactScore") == 88.9, str(res.get("impactScore")))

    if test_project_id:
        print(f"\n[11] POST /api/projects/{test_project_id}/impact (add metric 2)")
        m2_req = {
            "label": "Clean Energy Adoption",
            "before": 10.0,
            "after": 45.0,
            "unit": "% households",
        }
        code, res = request("POST", f"/api/projects/{test_project_id}/impact", m2_req)
        check("HTTP 201 Created", code == 201, str(code))
        if isinstance(res, dict):
            metrics = res.get("metrics", [])
            check("Has 2 metrics", len(metrics) == 2, str(len(metrics)))
            # Average improvement: (88.9 + 350.0) / 2 = 219.45 -> capped at 100.0
            check("ImpactScore capped at 100.0", res.get("impactScore") == 100.0, str(res.get("impactScore")))

    if test_project_id:
        print(f"\n[12] POST /api/projects/{test_project_id}/impact with empty label (expect 422)")
        code, res = request("POST", f"/api/projects/{test_project_id}/impact", {"label": "", "before": 10, "after": 20})
        check("HTTP 422 for empty metric label", code == 422, str(code))

    if test_project_id:
        print("\n[13] CamelCase field validation on GET /impact")
        code, res = request("GET", f"/api/projects/{test_project_id}/impact")
        check("HTTP 200 OK", code == 200, str(code))
        if isinstance(res, dict):
            required_camel = ["projectId", "impactScore", "status", "metrics", "beforeImage", "afterImage", "summary"]
            missing = [f for f in required_camel if f not in res]
            check("All required camelCase fields present", len(missing) == 0, f"missing={missing}")

            snake_keys = ["project_id", "impact_score", "before_image", "after_image"]
            leaked = [f for f in snake_keys if f in res]
            check("No snake_case fields leaked into response", len(leaked) == 0, f"leaked={leaked}")

finally:
    # ── Cleanup ─────────────────────────────────────────────────────────────────
    print("\n[CLEANUP] Removing isolated test records...")
    if test_challenge_id:
        try:
            client.table("pilots").delete().eq("challenge_id", test_challenge_id).execute()
            print(f"  -> Deleted test pilot: {test_challenge_id}")
        except Exception:
            pass
    if test_project_id:
        try:
            client.table("impact_metrics").delete().eq("project_id", test_project_id).execute()
            print(f"  -> Deleted test impact metrics for project: {test_project_id}")
        except Exception:
            pass
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
