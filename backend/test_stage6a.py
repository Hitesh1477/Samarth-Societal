"""
Stage 6A test suite — run from backend/ directory:
    python -u test_stage6a.py

Covers:
  1. Route registration (GET /api/dashboard/stats, GET /api/dashboard)
  2. Database connectivity
  3. GET /api/dashboard/stats structure and numeric fields
  4. GET /api/dashboard full analytics payload structure
  5. Chart array contents (challengesByCategory, priorityDistribution, reportsByDistrict, challengeLifecycle, monthlyReports)
  6. Map challenges array
  7. AI Insights array
  8. CamelCase response field validation
  9. Controlled test data impact on stats & charts
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


print("\n=== Stage 6A Test Suite: Dashboard & Analytics Backend ===\n")

# ── 1. Route Registration ──────────────────────────────────────────────────────

print("[1] GET /openapi.json  (route registration)")
code, body = request("GET", "/openapi.json")
paths = body.get("paths", {}) if isinstance(body, dict) else {}

check("OpenAPI reachable", code == 200, str(code))
check(
    "GET /api/dashboard/stats registered",
    "/api/dashboard/stats" in paths
    and "get" in paths.get("/api/dashboard/stats", {}),
)
check(
    "GET /api/dashboard registered",
    "/api/dashboard" in paths
    and "get" in paths.get("/api/dashboard", {}),
)

# ── Test Setup ─────────────────────────────────────────────────────────────────

client = get_supabase_admin_client()
test_challenge_id = str(uuid.uuid4())
test_problem_id = str(uuid.uuid4())

try:
    # Insert test challenge into DB
    chal_row = {
        "id": test_challenge_id,
        "title": "Stage 6A Test Challenge: Traffic Congestion at Paltan Bazaar",
        "category": "Transport",
        "subcategory": "Traffic Flow",
        "priority": 95,
        "priority_level": "HIGH",
        "status": "NEW",
        "affected_population": 15000,
        "report_count": 8,
        "district": "Kamrup Metropolitan",
        "location_name": "Paltan Bazaar Flyover",
        "lat": 26.1772,
        "lng": 91.7508,
    }
    client.table("challenges").insert(chal_row).execute()

    # Insert test problem into DB
    prob_row = {
        "id": test_problem_id,
        "title": "Severe Traffic Jam at Station Road",
        "description": "Daily bottleneck near railway station causing 45 min delay.",
        "category": "Transport",
        "subcategory": "Traffic Flow",
        "urgency": "HIGH",
        "affected_population": 4000,
        "location_lat": 26.1772,
        "location_lng": 91.7508,
        "location_name": "Paltan Bazaar",
        "location_district": "Kamrup Metropolitan",
        "reporter_name": "Citizen Reporter",
        "status": "SUBMITTED",
        "challenge_id": test_challenge_id,
    }
    client.table("problems").insert(prob_row).execute()

    # ── 2. GET /api/dashboard/stats ─────────────────────────────────────────────

    print("\n[2] GET /api/dashboard/stats")
    code, stats = request("GET", "/api/dashboard/stats")
    check("HTTP 200 OK", code == 200, str(code))
    check("Response is dict", isinstance(stats, dict), type(stats).__name__)
    if isinstance(stats, dict):
        required_stats_keys = [
            "totalReports",
            "validatedChallenges",
            "highPriority",
            "activeProjects",
            "completedPilots",
            "impactMeasured",
            "verifiedImpactPercent",
        ]
        missing = [k for k in required_stats_keys if k not in stats]
        check("All required stats fields present", len(missing) == 0, f"missing={missing}")
        check("totalReports >= 1", stats.get("totalReports", 0) >= 1, str(stats.get("totalReports")))
        check("validatedChallenges >= 1", stats.get("validatedChallenges", 0) >= 1, str(stats.get("validatedChallenges")))
        check("highPriority >= 1", stats.get("highPriority", 0) >= 1, str(stats.get("highPriority")))

        snake_keys = ["total_reports", "validated_challenges", "high_priority", "active_projects"]
        leaked = [k for k in snake_keys if k in stats]
        check("No snake_case fields leaked into stats", len(leaked) == 0, f"leaked={leaked}")

    # ── 3. GET /api/dashboard (full analytics payload) ──────────────────────────

    print("\n[3] GET /api/dashboard (full analytics payload)")
    code, dash = request("GET", "/api/dashboard")
    check("HTTP 200 OK", code == 200, str(code))
    check("Response is dict", isinstance(dash, dict), type(dash).__name__)
    if isinstance(dash, dict):
        required_dash_keys = [
            "stats",
            "challengesByCategory",
            "priorityDistribution",
            "reportsByDistrict",
            "challengeLifecycle",
            "monthlyReports",
            "mapChallenges",
            "aiInsights",
        ]
        missing = [k for k in required_dash_keys if k not in dash]
        check("All required DashboardData fields present", len(missing) == 0, f"missing={missing}")

        # Check chart arrays
        check("challengesByCategory is list", isinstance(dash.get("challengesByCategory"), list), type(dash.get("challengesByCategory")).__name__)
        check("priorityDistribution is list", isinstance(dash.get("priorityDistribution"), list), type(dash.get("priorityDistribution")).__name__)
        check("reportsByDistrict is list", isinstance(dash.get("reportsByDistrict"), list), type(dash.get("reportsByDistrict")).__name__)
        check("challengeLifecycle is list", isinstance(dash.get("challengeLifecycle"), list), type(dash.get("challengeLifecycle")).__name__)
        check("monthlyReports is list", isinstance(dash.get("monthlyReports"), list), type(dash.get("monthlyReports")).__name__)
        check("mapChallenges is list", isinstance(dash.get("mapChallenges"), list), type(dash.get("mapChallenges")).__name__)
        check("aiInsights is list", isinstance(dash.get("aiInsights"), list), type(dash.get("aiInsights")).__name__)

        # Validate chart data point shapes
        cbc = dash.get("challengesByCategory", [])
        if len(cbc) > 0:
            p0 = cbc[0]
            check("Chart point has name and value", "name" in p0 and "value" in p0, str(p0))

        # Validate lifecycle data point shapes
        lc = dash.get("challengeLifecycle", [])
        if len(lc) > 0:
            lc0 = lc[0]
            check("Lifecycle point has stage and value", "stage" in lc0 and "value" in lc0, str(lc0))

        # Validate mapChallenges includes our created challenge
        mc = dash.get("mapChallenges", [])
        if len(mc) > 0:
            mc_ids = [item.get("id") for item in mc if isinstance(item, dict)]
            check("Created challenge present in mapChallenges", test_challenge_id in mc_ids, f"found {len(mc_ids)} challenges")

        snake_keys = ["challenges_by_category", "priority_distribution", "reports_by_district", "challenge_lifecycle", "map_challenges", "ai_insights"]
        leaked = [k for k in snake_keys if k in dash]
        check("No snake_case fields leaked into DashboardData", len(leaked) == 0, f"leaked={leaked}")

finally:
    # ── Cleanup ─────────────────────────────────────────────────────────────────
    print("\n[CLEANUP] Removing isolated test records...")
    try:
        client.table("problems").delete().eq("id", test_problem_id).execute()
        print(f"  -> Deleted test problem: {test_problem_id}")
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
