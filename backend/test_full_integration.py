"""
Stage 7A — Full Backend End-to-End Integration Test Suite.
Run from backend/ directory:
    python -u test_full_integration.py

Executes the complete SAMARTH platform backend lifecycle sequentially:
  1. Health check (GET /health)
  2. Create a citizen problem (POST /api/problems)
  3. Get the problem (GET /api/problems/{id})
  4. Analyze the problem (POST /api/problems/{id}/analyze)
  5. Run duplicate detection (GET /api/problems/{id}/duplicates)
  6. Calculate priority (GET /api/problems/{id}/priority)
  7. Create a challenge (POST /api/challenges)
  8. Get challenge detail (GET /api/challenges/{id})
  9. Get challenge priority (GET /api/challenges/{id}/priority)
  10. Get solver matches (GET /api/challenges/{id}/solver-matches)
  11. Create a project linked to the challenge (POST /api/projects)
  12. Get project (GET /api/projects/{id})
  13. Add a milestone (POST /api/projects/{id}/milestones)
  14. Update milestone progress (PUT /api/milestones/{id})
  15. Verify project progress auto-update
  16. Create/update pilot (POST /api/challenges/{id}/pilot)
  17. Add impact metrics (POST /api/projects/{id}/impact)
  18. Retrieve impact summary (GET /api/projects/{id}/impact)
  19. Get dashboard statistics (GET /api/dashboard/stats)
  20. Get dashboard analytics (GET /api/dashboard)
  21. Get map challenges (GET /api/map/challenges)
  22. Error cases (404 for nonexistent IDs, 422 for invalid request payloads)
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


print("\n==================================================================")
print("  SAMARTH Platform — Full Integration Test Suite (Stage 7A)")
print("==================================================================\n")

client = get_supabase_admin_client()

# Unique UUID identifiers for isolated test lifecycle
problem_id: str | None = None
challenge_id: str | None = None
project_id: str | None = None
milestone_id: str | None = None

try:
    # ── 1. Health Check ────────────────────────────────────────────────────────
    print("[1] Health Check (GET /health)")
    code, res = request("GET", "/health")
    check("HTTP 200 OK", code == 200, str(code))
    check("Status is healthy/ok", isinstance(res, dict) and (res.get("status") in ["ok", "healthy"]), str(res))

    # ── 2. Create Citizen Problem ─────────────────────────────────────────────
    print("\n[2] Create Citizen Problem (POST /api/problems)")
    prob_req = {
        "title": "Stage 7A Integration: Severe Waterlogging at Zoo Road",
        "description": "Heavy monsoon rains caused 3ft waterlogging blocking emergency vehicles.",
        "category": "Infrastructure",
        "subcategory": "Drainage",
        "urgency": "HIGH",
        "affectedPopulation": 12000,
        "location": {
            "lat": 26.1664,
            "lng": 91.7781,
            "name": "Zoo Road Tiniali",
            "district": "Kamrup Metropolitan",
        },
        "evidence": [
            {"id": str(uuid.uuid4()), "type": "image", "url": "https://example.com/e1.jpg", "name": "flood_photo.jpg"}
        ],
        "reporterName": "Integration Test Citizen",
    }
    code, res = request("POST", "/api/problems", prob_req)
    check("HTTP 201 Created", code == 201, str(code))
    check("Response is dict", isinstance(res, dict))
    if isinstance(res, dict):
        problem_id = res.get("id")
        check("Has problem id", bool(problem_id), str(problem_id))
        check("Title matches", res.get("title") == prob_req["title"])
        check("Status is SUBMITTED", res.get("status") == "SUBMITTED")
        check("Location district matches", res.get("location", {}).get("district") == "Kamrup Metropolitan")
        check("ReporterName matches", res.get("reporterName") == prob_req["reporterName"])

    # ── 3. Get Problem ────────────────────────────────────────────────────────
    if problem_id:
        print(f"\n[3] Get Problem (GET /api/problems/{problem_id})")
        code, res = request("GET", f"/api/problems/{problem_id}")
        check("HTTP 200 OK", code == 200, str(code))
        check("Problem ID matches", res.get("id") == problem_id)
        check("Urgency matches", res.get("urgency") == "HIGH")

    # ── 4. Analyze Problem ─────────────────────────────────────────────────────
    if problem_id:
        print(f"\n[4] Analyze Problem (POST /api/problems/{problem_id}/analyze)")
        code, res = request("POST", f"/api/problems/{problem_id}/analyze")
        check("HTTP 200 OK", code == 200, str(code))
        if isinstance(res, dict):
            check("ProblemId matches", res.get("problemId") == problem_id)
            check("Structured statement present", bool(res.get("structuredStatement")))
            check("Confidence score between 0 and 1", 0.0 <= float(res.get("confidence", 0)) <= 1.0)
            check("Keywords is non-empty list", isinstance(res.get("keywords"), list) and len(res.get("keywords")) > 0)

    # ── 5. Run Duplicate Detection ─────────────────────────────────────────────
    if problem_id:
        print(f"\n[5] Run Duplicate Detection (GET /api/problems/{problem_id}/duplicates)")
        code, res = request("GET", f"/api/problems/{problem_id}/duplicates")
        check("HTTP 200 OK", code == 200, str(code))
        if isinstance(res, dict):
            check("ProblemId matches", res.get("problemId") == problem_id)
            check("TotalReports >= 1", res.get("totalReports", 0) >= 1)
            check("Reports is list", isinstance(res.get("reports"), list))

    # ── 6. Calculate Problem Priority ─────────────────────────────────────────
    if problem_id:
        print(f"\n[6] Calculate Problem Priority (GET /api/problems/{problem_id}/priority)")
        code, res = request("GET", f"/api/problems/{problem_id}/priority")
        check("HTTP 200 OK", code == 200, str(code))
        if isinstance(res, dict):
            check("Total priority score between 0 and 100", 0.0 <= float(res.get("total", -1)) <= 100.0)
            check("Level is valid enum (HIGH|MEDIUM|LOW)", res.get("level") in ["HIGH", "MEDIUM", "LOW"])
            check("Breakdown is present", isinstance(res.get("breakdown"), dict))

    # ── 7. Create Unified Challenge ────────────────────────────────────────────
    print("\n[7] Create Unified Challenge (POST /api/challenges)")
    chal_req = {
        "title": "Stage 7A Challenge: Zoo Road Urban Drainage Overhaul",
        "description": "Unified challenge addressing chronic urban flooding along RG Baruah Road Corridor.",
        "category": "Infrastructure",
        "subcategory": "Drainage",
        "location": {
            "lat": 26.1664,
            "lng": 91.7781,
            "name": "Zoo Road Tiniali",
            "district": "Kamrup Metropolitan",
        },
        "affectedPopulation": 55000,
        "sourceProblemId": problem_id,
    }
    code, res = request("POST", "/api/challenges", chal_req)
    check("HTTP 201 Created", code == 201, str(code))
    check("Response is dict", isinstance(res, dict))
    if isinstance(res, dict):
        challenge_id = res.get("id")
        check("Has challenge id", bool(challenge_id), str(challenge_id))
        check("Title matches", res.get("title") == chal_req["title"])
        check("Status is NEW on creation", res.get("status") == "NEW")
        check("Priority score between 0 and 100", 0.0 <= float(res.get("priority", -1)) <= 100.0)
        check("Priority level is valid", res.get("priorityLevel") in ["HIGH", "MEDIUM", "LOW"])

    # ── 8. Get Challenge Detail ────────────────────────────────────────────────
    if challenge_id:
        print(f"\n[8] Get Challenge Detail (GET /api/challenges/{challenge_id})")
        code, res = request("GET", f"/api/challenges/{challenge_id}")
        check("HTTP 200 OK", code == 200, str(code))
        if isinstance(res, dict):
            check("ID matches", res.get("id") == challenge_id)
            check("Timeline is list", isinstance(res.get("timeline"), list))
            check("PriorityBreakdown is dict", isinstance(res.get("priorityBreakdown"), dict))
            check("MatchedSolvers is list", isinstance(res.get("matchedSolvers"), list))

    # ── 9. Get Challenge Priority Endpoint ────────────────────────────────────
    if challenge_id:
        print(f"\n[9] Get Challenge Priority (GET /api/challenges/{challenge_id}/priority)")
        code, res = request("GET", f"/api/challenges/{challenge_id}/priority")
        check("HTTP 200 OK", code == 200, str(code))
        if isinstance(res, dict):
            check("Total priority score valid", 0.0 <= float(res.get("total", -1)) <= 100.0)
            check("Level valid", res.get("level") in ["HIGH", "MEDIUM", "LOW"])

    # ── 10. Get Solver Matches ─────────────────────────────────────────────────
    if challenge_id:
        print(f"\n[10] Get Solver Matches (GET /api/challenges/{challenge_id}/solver-matches)")
        code, res = request("GET", f"/api/challenges/{challenge_id}/solver-matches")
        check("HTTP 200 OK", code == 200, str(code))
        check("Response is list", isinstance(res, list))
        if isinstance(res, list) and len(res) > 0:
            s0 = res[0]
            check("Match has matchScore", "matchScore" in s0)
            check("Match has reasons list", isinstance(s0.get("reasons"), list))

    # ── 11. Create Project Linked to Challenge ──────────────────────────────────
    if challenge_id:
        print(f"\n[11] Create Project (POST /api/projects)")
        proj_req = {
            "challengeId": challenge_id,
            "title": "Automated Pumping & Stormwater Channel Expansion Project",
            "description": "Engineering intervention for Zoo Road flood management.",
            "team": [
                {"id": str(uuid.uuid4()), "name": "Dr. N. Sarma", "role": "Principal Investigator"},
                {"id": str(uuid.uuid4()), "name": "B. Das", "role": "Field Engineer"},
            ],
            "facultyMentor": "Prof. R. K. Medhi",
            "industryPartner": "Assam Urban Infrastructure Ltd",
        }
        code, res = request("POST", "/api/projects", proj_req)
        check("HTTP 201 Created", code == 201, str(code))
        check("Response is dict", isinstance(res, dict))
        if isinstance(res, dict):
            project_id = res.get("id")
            check("Has project id", bool(project_id), str(project_id))
            check("ChallengeId matches", res.get("challengeId") == challenge_id)
            check("ChallengeTitle populated", bool(res.get("challengeTitle")))
            check("Initial status is PROPOSAL", res.get("status") == "PROPOSAL")
            check("Initial progress is 0.0", res.get("progress") == 0.0)

    # ── 12. Get Project ────────────────────────────────────────────────────────
    if project_id:
        print(f"\n[12] Get Project (GET /api/projects/{project_id})")
        code, res = request("GET", f"/api/projects/{project_id}")
        check("HTTP 200 OK", code == 200, str(code))
        if isinstance(res, dict):
            check("ID matches", res.get("id") == project_id)
            check("Team size matches", len(res.get("team", [])) == 2)
            check("FacultyMentor matches", res.get("facultyMentor") == "Prof. R. K. Medhi")

    # ── 13. Add Milestone ──────────────────────────────────────────────────────
    if project_id:
        print(f"\n[13] Add Milestone (POST /api/projects/{project_id}/milestones)")
        ms_req = {
            "title": "Phase 1: Hydrological Survey & Equipment Setup",
            "status": "in_progress",
            "progress": 40.0,
            "dueDate": "2026-11-15",
            "evidenceCount": 3,
        }
        code, res = request("POST", f"/api/projects/{project_id}/milestones", ms_req)
        check("HTTP 201 Created", code == 201, str(code))
        if isinstance(res, dict):
            milestone_id = res.get("id")
            check("Has milestone id", bool(milestone_id), str(milestone_id))
            check("Status is in_progress", res.get("status") == "in_progress")
            check("Progress is 40.0", res.get("progress") == 40.0)

    # ── 14. Update Milestone Progress ──────────────────────────────────────────
    if milestone_id:
        print(f"\n[14] Update Milestone (PUT /api/milestones/{milestone_id})")
        u_ms_req = {
            "status": "completed",
            "progress": 100.0,
            "evidenceCount": 5,
        }
        code, res = request("PUT", f"/api/milestones/{milestone_id}", u_ms_req)
        check("HTTP 200 OK", code == 200, str(code))
        if isinstance(res, dict):
            check("Status updated to completed", res.get("status") == "completed")
            check("Progress updated to 100.0", res.get("progress") == 100.0)

    # ── 15. Verify Project Progress Auto-Update ────────────────────────────────
    if project_id:
        print(f"\n[15] Verify Project Progress (GET /api/projects/{project_id})")
        code, res = request("GET", f"/api/projects/{project_id}")
        check("HTTP 200 OK", code == 200, str(code))
        if isinstance(res, dict):
            check("Project progress updated to milestone progress (100.0)", res.get("progress") == 100.0, str(res.get("progress")))

    # ── 16. Create/Update Pilot ────────────────────────────────────────────────
    if challenge_id:
        print(f"\n[16] Create/Update Pilot (POST /api/challenges/{challenge_id}/pilot)")
        pilot_req = {
            "status": "active",
            "startDate": "2026-10-01",
            "endDate": "2027-02-28",
            "location": "Zoo Road RG Baruah Corridor",
            "participants": 600,
        }
        code, res = request("POST", f"/api/challenges/{challenge_id}/pilot", pilot_req)
        check("HTTP 201 Created", code == 201, str(code))
        if isinstance(res, dict):
            check("ChallengeId matches", res.get("challengeId") == challenge_id)
            check("Status is active", res.get("status") == "active")
            check("Participants is 600", res.get("participants") == 600)

    # ── 17. Add Impact Metrics ──────────────────────────────────────────────────
    if project_id:
        print(f"\n[17] Add Impact Metric (POST /api/projects/{project_id}/impact)")
        imp_req = {
            "label": "Peak Waterlogging Clearance Time",
            "before": 12.0,
            "after": 1.5,
            "unit": "hours",
            "summary": "Pumping array reduced clearance time from 12 hours to 1.5 hours.",
        }
        code, res = request("POST", f"/api/projects/{project_id}/impact", imp_req)
        check("HTTP 201 Created", code == 201, str(code))
        if isinstance(res, dict):
            check("ProjectId matches", res.get("projectId") == project_id)
            check("Status is measured", res.get("status") == "measured")
            metrics = res.get("metrics", [])
            check("Has 1 metric", len(metrics) == 1)
            if len(metrics) > 0:
                check("Improvement calculated (-87.5%)", metrics[0].get("improvement") == -87.5, str(metrics[0].get("improvement")))
                check("ImpactScore calculated (87.5)", res.get("impactScore") == 87.5, str(res.get("impactScore")))

    # ── 18. Retrieve Impact Summary ────────────────────────────────────────────
    if project_id:
        print(f"\n[18] Retrieve Impact Summary (GET /api/projects/{project_id}/impact)")
        code, res = request("GET", f"/api/projects/{project_id}/impact")
        check("HTTP 200 OK", code == 200, str(code))
        if isinstance(res, dict):
            check("ProjectId matches", res.get("projectId") == project_id)
            check("Metrics is non-empty list", len(res.get("metrics", [])) > 0)

    # ── 19. Get Dashboard Statistics ────────────────────────────────────────────
    print("\n[19] Get Dashboard Statistics (GET /api/dashboard/stats)")
    code, res = request("GET", "/api/dashboard/stats")
    check("HTTP 200 OK", code == 200, str(code))
    if isinstance(res, dict):
        check("totalReports >= 1", res.get("totalReports", 0) >= 1)
        check("validatedChallenges >= 1", res.get("validatedChallenges", 0) >= 1)
        check("highPriority >= 0", res.get("highPriority", 0) >= 0)
        check("verifiedImpactPercent is float", isinstance(res.get("verifiedImpactPercent"), (int, float)))

    # ── 20. Get Dashboard Analytics ──────────────────────────────────────────────
    print("\n[20] Get Dashboard Analytics (GET /api/dashboard)")
    code, res = request("GET", "/api/dashboard")
    check("HTTP 200 OK", code == 200, str(code))
    if isinstance(res, dict):
        check("stats is dict", isinstance(res.get("stats"), dict))
        check("challengesByCategory is list", isinstance(res.get("challengesByCategory"), list))
        check("priorityDistribution is list", isinstance(res.get("priorityDistribution"), list))
        check("reportsByDistrict is list", isinstance(res.get("reportsByDistrict"), list))
        check("challengeLifecycle is list", isinstance(res.get("challengeLifecycle"), list))
        check("monthlyReports is list", isinstance(res.get("monthlyReports"), list))
        check("mapChallenges is list", isinstance(res.get("mapChallenges"), list))
        check("aiInsights is list", isinstance(res.get("aiInsights"), list))

    # ── 21. Get Map Challenges ──────────────────────────────────────────────────
    print("\n[21] Get Map Challenges (GET /api/map/challenges)")
    code, res = request("GET", "/api/map/challenges")
    check("HTTP 200 OK", code == 200, str(code))
    if isinstance(res, dict):
        check("challenges is list", isinstance(res.get("challenges"), list))
        check("hotspots is list", isinstance(res.get("hotspots"), list))

        # Geospatial bounds check for all map challenges
        for mc in res.get("challenges", []):
            if isinstance(mc, dict):
                lat = float(mc.get("lat", 0))
                lng = float(mc.get("lng", 0))
                check(f"Latitude within [-90, 90] ({lat})", -90.0 <= lat <= 90.0)
                check(f"Longitude within [-180, 180] ({lng})", -180.0 <= lng <= 180.0)
                check("No zero-zero coordinates", not (lat == 0.0 and lng == 0.0))
                break

    # ── 22. Error Cases & Validation ─────────────────────────────────────────────
    print("\n[22] Error Cases (404 and 422 validations)")

    # 404 cases
    code, _ = request("GET", "/api/problems/00000000-0000-0000-0000-000000000000")
    check("404 for nonexistent problem ID", code == 404, str(code))

    code, _ = request("GET", "/api/challenges/00000000-0000-0000-0000-000000000000")
    check("404 for nonexistent challenge ID", code == 404, str(code))

    code, _ = request("GET", "/api/projects/00000000-0000-0000-0000-000000000000")
    check("404 for nonexistent project ID", code == 404, str(code))

    code, _ = request("PUT", "/api/milestones/00000000-0000-0000-0000-000000000000", {"status": "completed", "progress": 50.0})
    check("404 for nonexistent milestone ID", code == 404, str(code))

    code, _ = request("GET", "/api/projects/00000000-0000-0000-0000-000000000000/impact")
    check("404 for nonexistent project impact", code == 404, str(code))

    # 422 validation cases
    code, _ = request("POST", "/api/problems", {"title": "Short"})  # missing required fields
    check("422 for invalid problem payload", code == 422, str(code))

    if project_id:
        code, _ = request("PUT", f"/api/projects/{project_id}", {"progress": 150.0})
        check("422 for project progress > 100", code == 422, str(code))

    if milestone_id:
        code, _ = request("PUT", f"/api/milestones/{milestone_id}", {"progress": -20.0})
        check("422 for milestone progress < 0", code == 422, str(code))

finally:
    # ── Cleanup ─────────────────────────────────────────────────────────────────
    print("\n[CLEANUP] Removing isolated test records from database...")
    if milestone_id:
        try:
            client.table("milestones").delete().eq("id", milestone_id).execute()
            print(f"  -> Deleted test milestone: {milestone_id}")
        except Exception:
            pass
    if project_id:
        try:
            client.table("impact_metrics").delete().eq("project_id", project_id).execute()
            print(f"  -> Deleted test impact metrics: {project_id}")
        except Exception:
            pass
        try:
            client.table("projects").delete().eq("id", project_id).execute()
            print(f"  -> Deleted test project: {project_id}")
        except Exception:
            pass
    if challenge_id:
        try:
            client.table("pilots").delete().eq("challenge_id", challenge_id).execute()
            print(f"  -> Deleted test pilot: {challenge_id}")
        except Exception:
            pass
        try:
            client.table("challenges").delete().eq("id", challenge_id).execute()
            print(f"  -> Deleted test challenge: {challenge_id}")
        except Exception:
            pass
    if problem_id:
        try:
            client.table("problem_evidence").delete().eq("problem_id", problem_id).execute()
            client.table("problems").delete().eq("id", problem_id).execute()
            print(f"  -> Deleted test problem: {problem_id}")
        except Exception:
            pass
    print("  -> Cleanup complete.")

passed = sum(1 for r in _results if r)
total = len(_results)
print(f"\n==================================================")
print(f"Full Integration Results: {passed}/{total} assertions passed")
print(f"==================================================\n")
