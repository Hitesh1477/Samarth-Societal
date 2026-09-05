"""
Stage 2 test suite — run from backend/ directory:
    python test_stage2.py

Covers:
  - /health
  - OpenAPI route registration
  - POST /api/problems  (validation errors -> 422)
  - POST /api/problems  (real insert -> 201, or DB not configured -> 503)
  - GET  /api/problems  (list + filters)
  - GET  /api/problems/{id}
  - 404 handling
"""

import json
import sys
import urllib.request
import urllib.error

BASE = "http://localhost:8000"

# -- Resilient HTTP helper ------------------------------------------------------

def request(method: str, path: str, body: dict | None = None):
    """
    Returns (http_status_code, parsed_body_or_raw_text).
    Never raises — non-JSON bodies are returned as plain strings.
    Connection errors return (0, error_string).
    """
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


# -- Check helper ---------------------------------------------------------------

_results = []

def check(label: str, condition: bool, detail: str = "") -> bool:
    tag = "PASS" if condition else "FAIL"
    suffix = f"  ->  {detail}" if detail else ""
    print(f"  [{tag}] {label}{suffix}")
    _results.append(condition)
    return condition

def skip(label: str, reason: str):
    print(f"  [SKIP] {label}  ->  {reason}")


# ==============================================================================
print("\n=== Stage 2 Test Suite ===\n")

# -- 1. Health -----------------------------------------------------------------
print("[1] GET /health")
code, body = request("GET", "/health")
check("HTTP 200",                    code == 200,                     str(code))
check('body.status == "ok"',         isinstance(body, dict) and body.get("status") == "ok",  str(body))
check('body.service == "samarth-backend"',
      isinstance(body, dict) and body.get("service") == "samarth-backend", str(body))

# -- 2. OpenAPI route registration ---------------------------------------------
print("\n[2] GET /openapi.json  (route registration)")
code, body = request("GET", "/openapi.json")
paths = body.get("paths", {}) if isinstance(body, dict) else {}
check("OpenAPI reachable",                          code == 200,                              str(code))
check("POST /api/problems registered",              "/api/problems" in paths)
check("GET  /api/problems registered",              "/api/problems" in paths)
check("GET  /api/problems/{problem_id} registered", "/api/problems/{problem_id}" in paths)

# -- 3. Validation - empty body ------------------------------------------------
print("\n[3] POST /api/problems - empty body (expect 422)")
code, body = request("POST", "/api/problems", {})
check("422 Unprocessable Entity", code == 422, str(code))

# -- 4. Validation - invalid latitude -----------------------------------------
print("\n[4] POST /api/problems - lat=999 (expect 422)")
code, body = request("POST", "/api/problems", {
    "title": "Test",
    "description": "Test description that is long enough",
    "category": "Healthcare",
    "subcategory": "",
    "urgency": "HIGH",
    "affectedPopulation": 100,
    "location": {"lat": 999, "lng": 0, "name": "Test", "district": "Test"},
    "evidence": [],
    "reporterName": "Tester",
})
check("422 on lat out of range", code == 422, str(code))

# -- 5. Validation - unknown category -----------------------------------------
print("\n[5] POST /api/problems - bad category (expect 422)")
code, body = request("POST", "/api/problems", {
    "title": "Test",
    "description": "Test description that is long enough",
    "category": "INVALID_CATEGORY",
    "subcategory": "",
    "urgency": "HIGH",
    "affectedPopulation": 0,
    "location": {"lat": 19.0, "lng": 73.0, "name": "Mumbai", "district": "Mumbai"},
    "evidence": [],
    "reporterName": "Tester",
})
check("422 on unknown category", code == 422, str(code))

# -- 6. Validation - negative affectedPopulation -------------------------------
print("\n[6] POST /api/problems - affectedPopulation=-1 (expect 422)")
code, body = request("POST", "/api/problems", {
    "title": "Test",
    "description": "Test description that is long enough",
    "category": "Healthcare",
    "subcategory": "",
    "urgency": "MEDIUM",
    "affectedPopulation": -1,
    "location": {"lat": 19.0, "lng": 73.0, "name": "Mumbai", "district": "Mumbai"},
    "evidence": [],
    "reporterName": "Tester",
})
check("422 on negative affectedPopulation", code == 422, str(code))

# -- 7. POST - valid payload (Supabase required) -------------------------------
print("\n[7] POST /api/problems - valid payload")
VALID_PAYLOAD = {
    "title": "Road pothole near Government School",
    "description": "Large pothole on NH-48 near Government School causing accidents daily",
    "category": "Infrastructure",
    "subcategory": "Roads",
    "urgency": "HIGH",
    "affectedPopulation": 500,
    "location": {"lat": 19.076, "lng": 72.877, "name": "Andheri West", "district": "Mumbai"},
    "evidence": [],
    "reporterName": "Rahul Sharma",
}
code, body = request("POST", "/api/problems", VALID_PAYLOAD)

CREATED_ID = None
DB_AVAILABLE = False

if code == 201:
    DB_AVAILABLE = True
    CREATED_ID = body.get("id") if isinstance(body, dict) else None
    check("201 Created",                       True)
    check("id present",                        bool(CREATED_ID),                    str(CREATED_ID))
    check("camelCase: affectedPopulation",     "affectedPopulation" in body,        str(list(body)))
    check("camelCase: createdAt",              "createdAt" in body,                 str(list(body)))
    check("camelCase: reporterName",           "reporterName" in body,              str(list(body)))
    check("status == SUBMITTED",               body.get("status") == "SUBMITTED",   str(body.get("status")))
    check("challengeId is null",               body.get("challengeId") is None,     str(body.get("challengeId")))
    check("location.district correct",
          isinstance(body.get("location"), dict) and
          body["location"].get("district") == "Mumbai",
          str(body.get("location")))
    check("evidence is empty list",            body.get("evidence") == [],          str(body.get("evidence")))

elif code == 503:
    detail = body.get("detail", str(body)) if isinstance(body, dict) else str(body)
    print(f"  [BLOCKED] Database not configured - {detail}")
    skip("201 Created",                 "Supabase credentials not set")
    skip("camelCase field validation",  "Supabase credentials not set")
    skip("GET /api/problems",           "Supabase credentials not set")
    skip("GET /api/problems/{id}",      "Supabase credentials not set")
    skip("Filter tests",                "Supabase credentials not set")
    skip("404 test",                    "Supabase credentials not set - will test route shape anyway")

else:
    detail = body.get("detail", str(body)) if isinstance(body, dict) else str(body)
    check("201 Created", False, f"HTTP {code} - {detail}")

# -- 8-12. DB-dependent tests (only if insert succeeded) -----------------------
if DB_AVAILABLE and CREATED_ID:

    # 8. GET /api/problems (list)
    print("\n[8] GET /api/problems")
    code, body = request("GET", "/api/problems")
    check("HTTP 200",          code == 200,          str(code))
    check("returns a list",    isinstance(body, list), str(type(body)))
    if isinstance(body, list) and body:
        first = body[0]
        check("list item has id",                  "id" in first)
        check("list item camelCase affectedPopulation", "affectedPopulation" in first)
        check("list item camelCase createdAt",      "createdAt" in first)

    # 9. GET with category filter
    print("\n[9] GET /api/problems?category=Infrastructure")
    code, body = request("GET", "/api/problems?category=Infrastructure")
    check("HTTP 200", code == 200, str(code))
    if isinstance(body, list):
        wrong = [r for r in body if r.get("category") != "Infrastructure"]
        check("all results match category", len(wrong) == 0,
              f"{len(wrong)} non-matching items")

    # 10. GET with district filter
    print("\n[10] GET /api/problems?district=Mumbai")
    code, body = request("GET", "/api/problems?district=Mumbai")
    check("HTTP 200", code == 200, str(code))
    if isinstance(body, list):
        wrong = [r for r in body
                 if isinstance(r.get("location"), dict)
                 and r["location"].get("district") != "Mumbai"]
        check("all results match district", len(wrong) == 0,
              f"{len(wrong)} non-matching items")

    # 11. GET with search
    print("\n[11] GET /api/problems?search=pothole")
    code, body = request("GET", "/api/problems?search=pothole")
    check("HTTP 200",              code == 200,          str(code))
    check("search returns result", isinstance(body, list) and len(body) >= 1,
          f"got {len(body) if isinstance(body, list) else body} results")

    # 12. GET /api/problems/{id}
    print(f"\n[12] GET /api/problems/{CREATED_ID}")
    code, body = request("GET", f"/api/problems/{CREATED_ID}")
    check("HTTP 200",         code == 200,                           str(code))
    check("correct id",       isinstance(body, dict) and body.get("id") == CREATED_ID)
    check("has evidence list",isinstance(body, dict) and isinstance(body.get("evidence"), list))

    # 13. GET nonexistent -> 404
    print("\n[13] GET /api/problems/00000000-0000-0000-0000-000000000000 (expect 404)")
    code, body = request("GET", "/api/problems/00000000-0000-0000-0000-000000000000")
    check("HTTP 404",          code == 404,                          str(code))
    check("has detail field",  isinstance(body, dict) and "detail" in body, str(body))

else:
    # Even without DB, test the 404/503 route shape
    print("\n[8-12] BLOCKED - Supabase not configured")
    print("\n[13] GET /api/problems/00000000-0000-0000-0000-000000000000 (route shape)")
    code, body = request("GET", "/api/problems/00000000-0000-0000-0000-000000000000")
    check("404 or 503 (not 200 or crash)", code in (404, 503), str(code))
    check("JSON body returned",            isinstance(body, dict),   str(type(body)))
    check("has detail field",              isinstance(body, dict) and "detail" in body, str(body))

# -- Summary --------------------------------------------------------------------
passed = sum(_results)
total  = len(_results)
print(f"\n{'='*50}")
print(f"Results:  {passed}/{total} assertions passed")
if not DB_AVAILABLE:
    print("\n[CONFIGURATION REQUIRED]")
    print("  Supabase is NOT configured. To complete Stage 2 DB tests:")
    print("  1. Copy backend/.env.example to backend/.env")
    print("  2. Fill in SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
    print("  3. Deploy backend/supabase/schema.sql via Supabase SQL Editor")
    print("  4. Re-run:  python test_stage2.py")
else:
    print("\n[DB STATUS] Supabase connected - all DB tests ran against real database.")
print(f"{'='*50}\n")

sys.exit(0 if passed == total else 1)
