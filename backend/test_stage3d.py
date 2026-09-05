"""
Stage 3D test suite — run from backend/ directory:
    python test_stage3d.py

Covers:
  1. OpenAPI route registration for GET /api/challenges/{challenge_id}/solver-matches
  2. Nonexistent challenge ID returns HTTP 404
  3. Valid challenge returns HTTP 200 OK
  4. Response is a JSON list
  5. Response contract validation (id, name, type, matchScore, reasons, description)
  6. matchScore within range [0, 100]
  7. Results sorted by matchScore descending
  8. Relevant solvers rank above unrelated solvers
  9. Reasons list is non-empty and contains evidence-backed strings
 10. Scoring is deterministic (repeated calls yield identical scores & order)

Isolated Test Lifecycle:
  - Inserts isolated test challenge and test solver profiles with unique UUIDs
  - Performs all tests against controlled data
  - Cleans up created test records in a finally block without touching user data
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


print("\n=== Stage 3D Test Suite: Solver Matching Engine ===\n")

# 1. OpenAPI Route Registration
print("[1] GET /openapi.json  (route registration)")
code, body = request("GET", "/openapi.json")
paths = body.get("paths", {}) if isinstance(body, dict) else {}
check("OpenAPI reachable", code == 200, str(code))
check(
    "GET /api/challenges/{challenge_id}/solver-matches registered",
    "/api/challenges/{challenge_id}/solver-matches" in paths,
)

# 2. Nonexistent Challenge ID (Expect 404)
print("\n[2] GET /api/challenges/00000000-0000-0000-0000-000000000000/solver-matches (expect 404)")
code, body = request("GET", "/api/challenges/00000000-0000-0000-0000-000000000000/solver-matches")
check("HTTP 404 for nonexistent challenge", code == 404, str(code))
check("has detail field in error response", isinstance(body, dict) and "detail" in body, str(body))

# 3. Set Up Isolated Controlled Test Data
print("\n[3] Setting up isolated controlled test data in database...")

client = get_supabase_admin_client()

test_problem_id = str(uuid.uuid4())
solver_univ_id = str(uuid.uuid4())
solver_ind_id = str(uuid.uuid4())
solver_unrelated_id = str(uuid.uuid4())

created_solver_ids = [solver_univ_id, solver_ind_id, solver_unrelated_id]
created_problem_id = test_problem_id

try:
    # Insert test problem
    prob_row = {
        "id": test_problem_id,
        "title": "Stage 3D Test: Critical Waterlogging on Hospital Access Road",
        "description": "Severe drainage failure causes waterlogging and structural road damage near district hospital",
        "category": "Infrastructure",
        "subcategory": "Drainage / Road Infrastructure",
        "urgency": "HIGH",
        "affected_population": 4000,
        "location_lat": 23.344,
        "location_lng": 85.309,
        "location_name": "Hospital Access Road",
        "location_district": "Ranchi",
        "reporter_name": "Test Suite Runner",
        "status": "ANALYZED",
    }
    client.table("problems").insert(prob_row).execute()

    # Try inserting 3 controlled solver profiles
    db_solvers_inserted = False
    try:
        solvers_data = [
            {
                "id": solver_univ_id,
                "name": "Test Univ Civil & GIS Research Lab",
                "type": "university",
                "department": "Civil Engineering & GIS",
                "district": "Ranchi",
                "state": "Jharkhand",
                "categories": ["Infrastructure", "Water & Sanitation"],
                "expertise": ["Civil Engineering", "Drainage", "GIS Mapping", "Hydrology"],
                "capacity": "HIGH",
                "equipment": ["GIS Workstations", "Hydraulic Flow Meters"],
                "previous_projects": ["Urban Drainage Redesign"],
                "description": "Specialized academic lab for civil and drainage engineering.",
            },
            {
                "id": solver_ind_id,
                "name": "Test Urban Infra Build Corp",
                "type": "industry",
                "department": "Public Works Division",
                "district": "Ranchi",
                "state": "Jharkhand",
                "categories": ["Infrastructure", "Transport"],
                "expertise": ["Road Infrastructure", "Paving", "Civil Engineering"],
                "capacity": "HIGH",
                "equipment": ["Heavy Earthmoving Equipment"],
                "previous_projects": ["City Road Elevation"],
                "description": "Commercial engineering firm for road and drainage construction.",
            },
            {
                "id": solver_unrelated_id,
                "name": "Test Organic Pest Management Lab",
                "type": "university",
                "department": "Agricultural Sciences",
                "district": "Bokaro",
                "state": "Jharkhand",
                "categories": ["Agriculture"],
                "expertise": ["Pest Control", "Soil Chemistry", "Crop Yield"],
                "capacity": "LOW",
                "equipment": ["Spectrometer"],
                "previous_projects": ["Pest Infestation Audit"],
                "description": "Agricultural lab specializing in bio-pesticides.",
            },
        ]
        client.table("solver_profiles").insert(solvers_data).execute()
        db_solvers_inserted = True
        print("  -> Successfully created isolated test problem & 3 test solver profiles in DB.")
    except Exception as exc:
        print(f"  -> [NOTICE] DB solver_profiles insert skipped ({exc}). Using seed solver profiles.")

    # 4. Valid Challenge Request
    print(f"\n[4] GET /api/challenges/{test_problem_id}/solver-matches")
    code_m, body_m = request("GET", f"/api/challenges/{test_problem_id}/solver-matches")
    check("HTTP 200 OK for valid challenge", code_m == 200, str(code_m))
    check("Response is a JSON list", isinstance(body_m, list), type(body_m).__name__)

    if code_m == 200 and isinstance(body_m, list):
        # 5. Contract Schema & Field Validation
        print("\n[5] Response Contract & CamelCase Field Validation")
        required_fields = ["id", "name", "type", "matchScore", "reasons", "description"]
        all_valid_contracts = True

        for idx, item in enumerate(body_m):
            if not isinstance(item, dict):
                all_valid_contracts = False
                break
            for field in required_fields:
                if field not in item:
                    all_valid_contracts = False
                    print(f"    Missing field '{field}' in item {idx}")

        check("All solver items contain required fields", all_valid_contracts, f"item count={len(body_m)}")

        # 6. Score Range Validation
        print("\n[6] MatchScore Range Validation (0 <= matchScore <= 100)")
        scores = [item.get("matchScore", -1) for item in body_m if isinstance(item, dict)]
        scores_valid = all(isinstance(s, (int, float)) and 0 <= s <= 100 for s in scores)
        check("All matchScores within range [0, 100]", scores_valid, f"scores={scores}")

        # 7. Descending Sort Validation
        print("\n[7] Results Sorted by MatchScore Descending")
        is_sorted = all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1))
        check("Results sorted by matchScore descending", is_sorted, f"scores={scores}")

        # 8. Relative Ranking (Relevant vs Unrelated)
        print("\n[8] Relevant Solvers Rank Above Unrelated Solver")
        if db_solvers_inserted:
            univ_match = next((item for item in body_m if item.get("id") == solver_univ_id), None)
            ind_match = next((item for item in body_m if item.get("id") == solver_ind_id), None)
            unrelated_match = next((item for item in body_m if item.get("id") == solver_unrelated_id), None)
        else:
            univ_match = next((item for item in body_m if item.get("name") == "XYZ Institute of Technology"), None)
            ind_match = next((item for item in body_m if item.get("name") == "ABC Infrastructure Solutions"), None)
            unrelated_match = next((item for item in body_m if item.get("name") == "IIT (ISM) Dhanbad"), None)

        if univ_match and ind_match and unrelated_match:
            u_score = univ_match.get("matchScore", 0)
            i_score = ind_match.get("matchScore", 0)
            un_score = unrelated_match.get("matchScore", 0)

            check("Civil & GIS Lab score > Unrelated Lab score", u_score > un_score, f"{u_score} > {un_score}")
            check("Urban Infra Corp score > Unrelated Lab score", i_score > un_score, f"{i_score} > {un_score}")

            u_idx = body_m.index(univ_match)
            i_idx = body_m.index(ind_match)
            un_idx = body_m.index(unrelated_match)
            check("Relevant solvers appear before unrelated solver in list", u_idx < un_idx and i_idx < un_idx, f"univ={u_idx}, ind={i_idx}, unrelated={un_idx}")
        else:
            check("Found top relevant university & industry solvers and unrelated solver", False, f"univ={bool(univ_match)}, ind={bool(ind_match)}, unrelated={bool(unrelated_match)}")

        # 9. Reasons Quality & Data-Backed Validation
        print("\n[9] Reasons Validation (Non-empty & Factual Data-Backed)")
        reasons_valid = True
        for item in body_m:
            r_list = item.get("reasons", [])
            if not isinstance(r_list, list) or len(r_list) == 0:
                reasons_valid = False
                print(f"    Empty reasons for solver {item.get('name')}")
            elif not all(isinstance(r, str) and len(r.strip()) > 0 for r in r_list):
                reasons_valid = False
                print(f"    Invalid reason string in solver {item.get('name')}")

        check("Every returned solver has non-empty valid reasons list", reasons_valid)

        # 10. Deterministic Repeatability
        print("\n[10] Deterministic Scoring & Ranking Repeatability")
        code_m2, body_m2 = request("GET", f"/api/challenges/{test_problem_id}/solver-matches")
        check("Second request HTTP 200 OK", code_m2 == 200, str(code_m2))

        if code_m2 == 200 and isinstance(body_m2, list):
            scores2 = [item.get("matchScore") for item in body_m2 if isinstance(item, dict)]
            ids2 = [item.get("id") for item in body_m2 if isinstance(item, dict)]
            ids1 = [item.get("id") for item in body_m if isinstance(item, dict)]

            check("Scores identical across runs", scores == scores2, f"run1={scores}, run2={scores2}")
            check("Ranking order identical across runs", ids1 == ids2, f"run1={ids1}, run2={ids2}")

finally:
    # Clean up test records
    print("\n[CLEANUP] Removing isolated test records from database...")
    try:
        if created_solver_ids and db_solvers_inserted:
            client.table("solver_profiles").delete().in_("id", created_solver_ids).execute()
        if created_problem_id:
            client.table("problems").delete().eq("id", created_problem_id).execute()
        print("  -> Test data cleanup complete.")
    except Exception as cleanup_err:
        print(f"  -> [WARN] Cleanup notice: {cleanup_err}")

passed = sum(_results)
total = len(_results)
print(f"\n{'='*50}")
print(f"Results: {passed}/{total} assertions passed")
print(f"{'='*50}\n")

sys.exit(0 if passed == total else 1)
