"""
Stage 4A test suite — run from backend/ directory:
    python -u test_stage4a.py

Covers:
  1.  Route registration (POST /api/challenges, GET /api/challenges,
       GET /api/challenges/{id})
  2.  Create challenge (POST /api/challenges)
  3.  Get challenge list (GET /api/challenges)
  4.  Get challenge by ID (GET /api/challenges/{id})
  5.  404 for nonexistent challenge ID
  6.  Correct camelCase response fields
  7.  Correct challenge status (NEW on creation)
  8.  Correct report count
  9.  Challenge detail structure (timeline, duplicateCluster, priorityBreakdown, etc.)
  10. Existing priority and solver-match endpoints still respond correctly

Isolated test lifecycle:
  - Creates a challenge and a linked problem with unique UUIDs.
  - All assertions run against controlled test data.
  - finally block cleans up all created records without touching real data.
"""

import json
import sys
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


print("\n=== Stage 4A Test Suite: Challenge Creation & Challenge APIs ===\n")

# ── 1. Route Registration ──────────────────────────────────────────────────────

print("[1] GET /openapi.json  (route registration)")
code, body = request("GET", "/openapi.json")
paths = body.get("paths", {}) if isinstance(body, dict) else {}

check("OpenAPI reachable", code == 200, str(code))
check("POST /api/challenges registered", "/api/challenges" in paths and "post" in paths.get("/api/challenges", {}))
check("GET  /api/challenges registered", "/api/challenges" in paths and "get" in paths.get("/api/challenges", {}))
check(
    "GET  /api/challenges/{challenge_id} registered",
    "/api/challenges/{challenge_id}" in paths,
)
check(
    "GET  /api/challenges/{challenge_id}/priority still registered",
    "/api/challenges/{challenge_id}/priority" in paths,
)
check(
    "GET  /api/challenges/{challenge_id}/solver-matches still registered",
    "/api/challenges/{challenge_id}/solver-matches" in paths,
)

# ── Test Data Setup ────────────────────────────────────────────────────────────

client = get_supabase_admin_client()

test_challenge_id: str | None = None
test_problem_id: str | None = None
created_challenge_ids: list[str] = []
created_problem_ids: list[str] = []

try:
    # ── 2. Create Challenge ────────────────────────────────────────────────────

    print("\n[2] POST /api/challenges (create challenge)")
    create_body = {
        "title": "Stage 4A Test: Waterlogging in Market Area",
        "description": "Severe waterlogging blocks access to main market area during monsoon",
        "category": "Infrastructure",
        "subcategory": "Drainage",
        "location": {
            "lat": 23.344,
            "lng": 85.309,
            "name": "Market Road",
            "district": "Ranchi",
        },
        "affectedPopulation": 3500,
    }

    code_c, body_c = request("POST", "/api/challenges", create_body)
    check("HTTP 201 Created", code_c == 201, str(code_c))
    check("Response is a dict", isinstance(body_c, dict), type(body_c).__name__)

    if code_c == 201 and isinstance(body_c, dict):
        test_challenge_id = body_c.get("id")
        if test_challenge_id:
            created_challenge_ids.append(test_challenge_id)
        check("Has id field", bool(test_challenge_id), str(test_challenge_id))
        check("Has title field", body_c.get("title") == create_body["title"], str(body_c.get("title")))
        check("Has category field", body_c.get("category") == "Infrastructure", str(body_c.get("category")))
    else:
        print(f"  [WARN] Unexpected create response: {body_c}")

    # ── 3. Get Challenge List ──────────────────────────────────────────────────

    print("\n[3] GET /api/challenges (challenge list)")
    code_l, body_l = request("GET", "/api/challenges")
    check("HTTP 200 OK", code_l == 200, str(code_l))
    check("Response is a list", isinstance(body_l, list), type(body_l).__name__)

    if test_challenge_id and isinstance(body_l, list):
        ids_in_list = [item.get("id") for item in body_l if isinstance(item, dict)]
        check("Created challenge appears in list", test_challenge_id in ids_in_list, f"list size={len(body_l)}")

    # Filter by category
    code_lf, body_lf = request("GET", "/api/challenges?category=Infrastructure")
    check("Category filter HTTP 200", code_lf == 200, str(code_lf))
    check("Category filter returns list", isinstance(body_lf, list), type(body_lf).__name__)

    # ── 4. Get Challenge By ID ─────────────────────────────────────────────────

    if test_challenge_id:
        print(f"\n[4] GET /api/challenges/{test_challenge_id}")
        code_g, body_g = request("GET", f"/api/challenges/{test_challenge_id}")
        check("HTTP 200 OK", code_g == 200, str(code_g))
        check("Response is a dict", isinstance(body_g, dict), type(body_g).__name__)
    else:
        print("\n[4] Skipping GET by ID — no challenge ID available")
        check("GET challenge by ID (skipped)", False, "no challenge id")

    # ── 5. 404 for Nonexistent Challenge ──────────────────────────────────────

    print("\n[5] GET /api/challenges/00000000-0000-0000-0000-000000000000 (expect 404)")
    code_nf, body_nf = request("GET", "/api/challenges/00000000-0000-0000-0000-000000000000")
    check("HTTP 404 for nonexistent challenge", code_nf == 404, str(code_nf))
    check("Error response has detail field", isinstance(body_nf, dict) and "detail" in body_nf, str(body_nf))

    # ── 6. camelCase Fields ────────────────────────────────────────────────────

    print("\n[6] CamelCase field validation")
    if test_challenge_id and isinstance(body_g, dict) and code_g == 200:
        required_camel_fields = [
            "id", "title", "category", "subcategory", "location",
            "reportCount", "affectedPopulation", "priority",
            "priorityLevel", "status", "createdAt", "description",
        ]
        missing = [f for f in required_camel_fields if f not in body_g]
        check("All required camelCase fields present", len(missing) == 0, f"missing={missing}")

        # Ensure snake_case aliases are NOT in response
        snake_case_fields = ["report_count", "affected_population", "priority_level", "created_at"]
        snake_present = [f for f in snake_case_fields if f in body_g]
        check("No snake_case fields leaked into response", len(snake_present) == 0, f"leaked={snake_present}")
    else:
        check("camelCase validation (skipped — no valid challenge)", False, "no challenge detail")

    # ── 7. Correct Challenge Status ────────────────────────────────────────────

    print("\n[7] Challenge status validation")
    if test_challenge_id and isinstance(body_g, dict) and code_g == 200:
        challenge_status = body_g.get("status")
        check("Status is NEW on creation", challenge_status == "NEW", str(challenge_status))
    else:
        check("Status validation (skipped — no valid challenge)", False, "no challenge detail")

    # ── 8. Correct Report Count ────────────────────────────────────────────────

    print("\n[8] Report count validation")

    # Insert a problem linked to the challenge
    if test_challenge_id:
        test_problem_id = str(uuid.uuid4())
        created_problem_ids.append(test_problem_id)
        prob_row = {
            "id": test_problem_id,
            "title": "Stage 4A Linked Problem: Waterlogging Report",
            "description": "Severe waterlogging on access road to market",
            "category": "Infrastructure",
            "subcategory": "Drainage",
            "urgency": "HIGH",
            "affected_population": 3500,
            "location_lat": 23.344,
            "location_lng": 85.309,
            "location_name": "Market Road",
            "location_district": "Ranchi",
            "reporter_name": "Stage 4A Test Suite",
            "status": "ANALYZED",
            "challenge_id": test_challenge_id,
        }
        try:
            client.table("problems").insert(prob_row).execute()
            print(f"  -> Inserted test problem {test_problem_id} linked to challenge {test_challenge_id}")
        except Exception as exc:
            print(f"  -> [WARN] Could not insert test problem: {exc}")

        # Re-fetch detail after linking problem
        code_g2, body_g2 = request("GET", f"/api/challenges/{test_challenge_id}")
        if code_g2 == 200 and isinstance(body_g2, dict):
            rc = body_g2.get("reportCount", 0)
            check("reportCount >= 1 after linking problem", rc >= 1, str(rc))
        else:
            check("Re-fetch challenge detail HTTP 200", code_g2 == 200, str(code_g2))
    else:
        check("Report count validation (skipped — no challenge)", False, "no challenge id")

    # ── 9. Challenge Detail Structure ──────────────────────────────────────────

    print("\n[9] Challenge detail structure validation")
    if test_challenge_id:
        code_d, body_d = request("GET", f"/api/challenges/{test_challenge_id}")
        check("Detail HTTP 200 OK", code_d == 200, str(code_d))

        if code_d == 200 and isinstance(body_d, dict):
            # Timeline
            tl = body_d.get("timeline")
            check("timeline is a list", isinstance(tl, list), type(tl).__name__)
            if isinstance(tl, list) and tl:
                tl_item = tl[0]
                check("timeline item has id/label/status", all(k in tl_item for k in ("id", "label", "status")), str(tl_item.keys()))
                has_current = any(e.get("status") == "current" for e in tl)
                check("timeline has exactly one 'current' event", sum(1 for e in tl if e.get("status") == "current") == 1)

            # duplicateCluster
            dc = body_d.get("duplicateCluster")
            check("duplicateCluster is present", dc is not None, str(type(dc)))
            if dc is not None:
                check("duplicateCluster.problemId present", "problemId" in dc, str(dc.keys()))
                check("duplicateCluster.totalReports >= 1", dc.get("totalReports", 0) >= 1, str(dc.get("totalReports")))

            # priorityBreakdown
            pb = body_d.get("priorityBreakdown")
            check("priorityBreakdown is present", pb is not None, str(type(pb)))
            if pb is not None:
                pb_fields = ["safetyRisk", "populationImpact", "recurrence", "evidence", "locationRisk"]
                missing_pb = [f for f in pb_fields if f not in pb]
                check("priorityBreakdown has all sub-fields", len(missing_pb) == 0, f"missing={missing_pb}")

            # priorityExplanation
            pe = body_d.get("priorityExplanation")
            check("priorityExplanation is a non-empty string", isinstance(pe, str) and len(pe) > 0, str(pe))

            # reports
            reps = body_d.get("reports")
            check("reports is a list", isinstance(reps, list), type(reps).__name__)

            # evidence
            ev = body_d.get("evidence")
            check("evidence is a list", isinstance(ev, list), type(ev).__name__)

            # matchedSolvers
            ms = body_d.get("matchedSolvers")
            check("matchedSolvers is a list", isinstance(ms, list), type(ms).__name__)

            # keywords / confidence
            check("keywords is a list", isinstance(body_d.get("keywords"), list))
            conf = body_d.get("confidence")
            check("confidence is a number", isinstance(conf, (int, float)), str(conf))

            # structuredStatement
            check("structuredStatement present", "structuredStatement" in body_d)
        else:
            check("Detail body is dict (skipped)", False, str(type(body_d)))
    else:
        check("Challenge detail structure (skipped — no challenge)", False, "no challenge id")

    # ── 10. Existing Endpoints Still Work ──────────────────────────────────────

    print("\n[10] Existing Stage 3C/3D endpoints still respond correctly")

    if test_challenge_id:
        # Priority endpoint
        code_p, body_p = request("GET", f"/api/challenges/{test_challenge_id}/priority")
        check("GET /priority HTTP 200", code_p == 200, str(code_p))
        if code_p == 200 and isinstance(body_p, dict):
            p_fields = ["challengeId", "total", "level", "breakdown", "explanation"]
            missing_p = [f for f in p_fields if f not in body_p]
            check("Priority response has all required fields", len(missing_p) == 0, f"missing={missing_p}")

        # Solver matches endpoint
        code_sm, body_sm = request("GET", f"/api/challenges/{test_challenge_id}/solver-matches")
        check("GET /solver-matches HTTP 200", code_sm == 200, str(code_sm))
        check("Solver-matches response is a list", isinstance(body_sm, list), type(body_sm).__name__)
        if isinstance(body_sm, list) and body_sm:
            sm_fields = ["id", "name", "type", "matchScore", "reasons", "description"]
            missing_sm = [f for f in sm_fields if f not in body_sm[0]]
            check("Solver match items have required fields", len(missing_sm) == 0, f"missing={missing_sm}")
    else:
        check("Priority endpoint check (skipped — no challenge id)", False)
        check("Solver-matches endpoint check (skipped — no challenge id)", False)

    # 404 for nonexistent on sub-routes
    nf_id = "00000000-0000-0000-0000-000000000000"
    code_p404, _ = request("GET", f"/api/challenges/{nf_id}/priority")
    check("GET /priority returns 404 for nonexistent", code_p404 == 404, str(code_p404))

    code_sm404, _ = request("GET", f"/api/challenges/{nf_id}/solver-matches")
    check("GET /solver-matches returns 404 for nonexistent", code_sm404 == 404, str(code_sm404))

finally:
    print("\n[CLEANUP] Removing isolated test records from database...")
    try:
        if created_problem_ids:
            client.table("problems").delete().in_("id", created_problem_ids).execute()
            print(f"  -> Deleted test problems: {created_problem_ids}")
        if created_challenge_ids:
            client.table("challenges").delete().in_("id", created_challenge_ids).execute()
            print(f"  -> Deleted test challenges: {created_challenge_ids}")
        print("  -> Test data cleanup complete.")
    except Exception as cleanup_err:
        print(f"  -> [WARN] Cleanup notice: {cleanup_err}")

passed = sum(_results)
total = len(_results)
print(f"\n{'='*50}")
print(f"Results: {passed}/{total} assertions passed")
print(f"{'='*50}\n")

sys.exit(0 if passed == total else 1)
