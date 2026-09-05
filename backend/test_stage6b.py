"""
Stage 6B test suite — run from backend/ directory:
    python -u test_stage6b.py

Covers:
  1. Route registration (GET /api/map/challenges)
  2. GET /api/map/challenges response structure (challenges, hotspots)
  3. Marker fields (id, title, lat, lng, priority, priorityLevel, reportCount, affectedPopulation, status, category, district)
  4. Valid latitude/longitude enforcement (-90 to 90, -180 to 180, excludes invalid (0,0) or null coordinates)
  5. Hotspot structure & sorting (count descending)
  6. Category filter (?category=...)
  7. Priority filter (?priority=HIGH|MEDIUM|LOW)
  8. District filter (?district=...)
  9. CamelCase response field validation
  10. Isolated test data setup and cleanup
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


print("\n=== Stage 6B Test Suite: Map & Geospatial API ===\n")

# ── 1. Route Registration ──────────────────────────────────────────────────────

print("[1] GET /openapi.json  (route registration)")
code, body = request("GET", "/openapi.json")
paths = body.get("paths", {}) if isinstance(body, dict) else {}

check("OpenAPI reachable", code == 200, str(code))
check(
    "GET /api/map/challenges registered",
    "/api/map/challenges" in paths
    and "get" in paths.get("/api/map/challenges", {}),
)

# ── Test Data Setup ────────────────────────────────────────────────────────────

client = get_supabase_admin_client()
c1_id = str(uuid.uuid4())
c2_id = str(uuid.uuid4())
c_invalid_id = str(uuid.uuid4())

try:
    # 1. Challenge with valid coords in Ranchi
    client.table("challenges").insert({
        "id": c1_id,
        "title": "Stage 6B Valid Challenge 1: Ranchi Water Supply",
        "category": "Water & Sanitation",
        "subcategory": "Pipeline",
        "priority": 92,
        "priority_level": "HIGH",
        "status": "NEW",
        "affected_population": 10000,
        "report_count": 6,
        "district": "Ranchi",
        "location_name": "Main Road Ranchi",
        "lat": 23.3441,
        "lng": 85.3096,
    }).execute()

    # 2. Challenge with valid coords in Ranchi (for hotspot count test)
    client.table("challenges").insert({
        "id": c2_id,
        "title": "Stage 6B Valid Challenge 2: Ranchi Waste Management",
        "category": "Waste Management",
        "subcategory": "Collection",
        "priority": 45,
        "priority_level": "LOW",
        "status": "NEW",
        "affected_population": 3000,
        "report_count": 2,
        "district": "Ranchi",
        "location_name": "Kanke Road",
        "lat": 23.3800,
        "lng": 85.3200,
    }).execute()

    # 3. Challenge with invalid (0, 0) coords (should be excluded)
    client.table("challenges").insert({
        "id": c_invalid_id,
        "title": "Stage 6B Invalid Coords Challenge",
        "category": "Infrastructure",
        "subcategory": "Roads",
        "priority": 50,
        "priority_level": "MEDIUM",
        "status": "NEW",
        "affected_population": 500,
        "report_count": 1,
        "district": "NullIsland",
        "location_name": "Zero Island",
        "lat": 0.0,
        "lng": 0.0,
    }).execute()

    # ── 2. Basic GET /api/map/challenges ───────────────────────────────────────

    print("\n[2] GET /api/map/challenges (fetch map data)")
    code, map_data = request("GET", "/api/map/challenges")
    check("HTTP 200 OK", code == 200, str(code))
    check("Response is dict", isinstance(map_data, dict), type(map_data).__name__)
    if isinstance(map_data, dict):
        check("Has challenges list", isinstance(map_data.get("challenges"), list), type(map_data.get("challenges")).__name__)
        check("Has hotspots list", isinstance(map_data.get("hotspots"), list), type(map_data.get("hotspots")).__name__)

        challenges = map_data.get("challenges", [])
        c_ids = [c.get("id") for c in challenges if isinstance(c, dict)]

        check("Valid challenge 1 included in map", c1_id in c_ids, f"found {len(c_ids)} map challenges")
        check("Valid challenge 2 included in map", c2_id in c_ids, f"found {len(c_ids)} map challenges")
        check("Invalid (0,0) challenge excluded from map", c_invalid_id not in c_ids, "excluded invalid coords")

        # ── 3. Marker Fields & Coordinate Bounds ─────────────────────────────

        print("\n[3] Marker Field Validation & Geospatial Bounds")
        target_c = next((c for c in challenges if c.get("id") == c1_id), None)
        check("Target challenge marker present", target_c is not None)
        if target_c:
            check("lat is float between -90 and 90", -90.0 <= float(target_c.get("lat", 999)) <= 90.0, str(target_c.get("lat")))
            check("lng is float between -180 and 180", -180.0 <= float(target_c.get("lng", 999)) <= 180.0, str(target_c.get("lng")))
            check("priority is numeric", isinstance(target_c.get("priority"), (int, float)), str(target_c.get("priority")))
            check("priorityLevel is HIGH", target_c.get("priorityLevel") == "HIGH", str(target_c.get("priorityLevel")))
            check("reportCount matches", target_c.get("reportCount") == 6, str(target_c.get("reportCount")))
            check("affectedPopulation matches", target_c.get("affectedPopulation") == 10000, str(target_c.get("affectedPopulation")))
            check("district matches", target_c.get("district") == "Ranchi", str(target_c.get("district")))

        # ── 4. Hotspot Aggregation & Sorting ─────────────────────────────────

        print("\n[4] Hotspot Aggregation & Sorting")
        hotspots = map_data.get("hotspots", [])
        check("Hotspots list non-empty", len(hotspots) > 0, f"count={len(hotspots)}")
        if len(hotspots) > 0:
            h0 = hotspots[0]
            check("Hotspot has name and count", "name" in h0 and "count" in h0, str(h0))
            # Verify descending order
            counts = [h.get("count", 0) for h in hotspots if isinstance(h, dict)]
            is_sorted = all(counts[i] >= counts[i + 1] for i in range(len(counts) - 1))
            check("Hotspots sorted by count descending", is_sorted, f"counts={counts[:5]}")

    # ── 5. Category Filter ────────────────────────────────────────────────────

    print("\n[5] GET /api/map/challenges?category=Water%20%26%20Sanitation")
    code, filtered_cat = request("GET", "/api/map/challenges?category=Water%20%26%20Sanitation")
    check("HTTP 200 OK", code == 200, str(code))
    if isinstance(filtered_cat, dict):
        cat_c_ids = [c.get("id") for c in filtered_cat.get("challenges", []) if isinstance(c, dict)]
        check("Water & Sanitation challenge included", c1_id in cat_c_ids)
        check("Waste Management challenge filtered out", c2_id not in cat_c_ids)

    # ── 6. Priority Filter ────────────────────────────────────────────────────

    print("\n[6] GET /api/map/challenges?priority=HIGH")
    code, filtered_prio = request("GET", "/api/map/challenges?priority=HIGH")
    check("HTTP 200 OK", code == 200, str(code))
    if isinstance(filtered_prio, dict):
        prio_c_ids = [c.get("id") for c in filtered_prio.get("challenges", []) if isinstance(c, dict)]
        check("HIGH priority challenge included", c1_id in prio_c_ids)
        check("LOW priority challenge filtered out", c2_id not in prio_c_ids)

    # ── 7. District Filter ────────────────────────────────────────────────────

    print("\n[7] GET /api/map/challenges?district=Ranchi")
    code, filtered_dist = request("GET", "/api/map/challenges?district=Ranchi")
    check("HTTP 200 OK", code == 200, str(code))
    if isinstance(filtered_dist, dict):
        dist_c_ids = [c.get("id") for c in filtered_dist.get("challenges", []) if isinstance(c, dict)]
        check("Ranchi challenge 1 included", c1_id in dist_c_ids)
        check("Ranchi challenge 2 included", c2_id in dist_c_ids)

    # ── 8. CamelCase Response Field Validation ─────────────────────────────────

    print("\n[8] CamelCase response field validation")
    code, map_res = request("GET", "/api/map/challenges")
    check("HTTP 200 OK", code == 200, str(code))
    if isinstance(map_res, dict) and map_res.get("challenges"):
        first_c = map_res["challenges"][0]
        required_camel = [
            "id",
            "title",
            "lat",
            "lng",
            "priority",
            "priorityLevel",
            "reportCount",
            "affectedPopulation",
            "status",
            "category",
            "district",
        ]
        missing = [f for f in required_camel if f not in first_c]
        check("All required camelCase fields present in MapChallenge", len(missing) == 0, f"missing={missing}")

        snake_keys = ["priority_level", "report_count", "affected_population"]
        leaked = [f for f in snake_keys if f in first_c]
        check("No snake_case fields leaked into MapChallenge response", len(leaked) == 0, f"leaked={leaked}")

finally:
    # ── Cleanup ─────────────────────────────────────────────────────────────────
    print("\n[CLEANUP] Removing isolated test records...")
    for cid in [c1_id, c2_id, c_invalid_id]:
        try:
            client.table("challenges").delete().eq("id", cid).execute()
            print(f"  -> Deleted test challenge: {cid}")
        except Exception:
            pass
    print("  -> Cleanup complete.")

passed = sum(1 for r in _results if r)
total = len(_results)
print(f"\n==================================================")
print(f"Results: {passed}/{total} assertions passed")
print(f"==================================================\n")
