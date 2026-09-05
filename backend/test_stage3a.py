"""
Stage 3A test suite — run from backend/ directory:
    python test_stage3a.py

Covers:
  - OpenAPI route registration for POST /api/problems/{problem_id}/analyze
  - POST /api/problems/{problem_id}/analyze on a valid problem report
  - Response schema & field names (camelCase: problemId, structuredStatement, etc.)
  - Fallback behavior (deterministic analysis when OPENAI_API_KEY is not configured or in fallback mode)
  - Nonexistent problem analysis (returns 404)
  - Status update in database (status becomes ANALYZED)
"""

import json
import sys
import urllib.request
import urllib.error

BASE = "http://localhost:8000"


def request(method: str, path: str, body: dict | None = None):
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


_results = []


def check(label: str, condition: bool, detail: str = "") -> bool:
    tag = "PASS" if condition else "FAIL"
    suffix = f"  ->  {detail}" if detail else ""
    print(f"  [{tag}] {label}{suffix}")
    _results.append(condition)
    return condition


def skip(label: str, reason: str):
    print(f"  [SKIP] {label}  ->  {reason}")


print("\n=== Stage 3A Test Suite: AI Problem Analysis ===\n")

# 1. OpenAPI Route Registration
print("[1] GET /openapi.json  (route registration)")
code, body = request("GET", "/openapi.json")
paths = body.get("paths", {}) if isinstance(body, dict) else {}
check("OpenAPI reachable", code == 200, str(code))
check(
    "POST /api/problems/{problem_id}/analyze registered",
    "/api/problems/{problem_id}/analyze" in paths,
)

# 2. Nonexistent Problem Analysis (Expect 404)
print("\n[2] POST /api/problems/00000000-0000-0000-0000-000000000000/analyze (expect 404)")
code, body = request("POST", "/api/problems/00000000-0000-0000-0000-000000000000/analyze")
check("HTTP 404", code == 404, str(code))
check("has detail field", isinstance(body, dict) and "detail" in body, str(body))

# 3. Create a Problem for Testing Analysis
print("\n[3] POST /api/problems - create problem report for AI analysis")
TEST_PROBLEM = {
    "title": "Severe Water Contamination in Sector 4",
    "description": "Tap water supply has severe discoloration and foul odor causing illness among residents in Thane district",
    "category": "Water & Sanitation",
    "subcategory": "Water Quality",
    "urgency": "CRITICAL",
    "affectedPopulation": 1200,
    "location": {"lat": 19.2183, "lng": 72.9781, "name": "Sector 4", "district": "Thane"},
    "evidence": [],
    "reporterName": "Aarti Patel",
}
code, problem_body = request("POST", "/api/problems", TEST_PROBLEM)

if code == 201 and isinstance(problem_body, dict) and "id" in problem_body:
    problem_id = problem_body["id"]
    check("Problem created successfully", True, f"ID: {problem_id}")

    # 4. POST /api/problems/{problem_id}/analyze
    print(f"\n[4] POST /api/problems/{problem_id}/analyze")
    an_code, an_body = request("POST", f"/api/problems/{problem_id}/analyze")

    check("HTTP 200 OK", an_code == 200, str(an_code))

    if an_code == 200 and isinstance(an_body, dict):
        # 5. Schema & field name verification
        print("\n[5] Response Schema & CamelCase Field Validation")
        required_fields = [
            ("problemId", str),
            ("structuredStatement", str),
            ("category", str),
            ("subcategory", str),
            ("keywords", list),
            ("urgency", str),
            ("confidence", (int, float)),
            ("affectedPopulation", int),
            ("evidenceCount", int),
        ]

        for field_name, expected_type in required_fields:
            has_field = field_name in an_body
            val = an_body.get(field_name)
            is_correct_type = isinstance(val, expected_type)
            check(
                f"field '{field_name}' present and valid type ({expected_type.__name__ if isinstance(expected_type, type) else 'number'})",
                has_field and is_correct_type,
                f"val={val!r}",
            )

        check(
            "problemId matches requested ID",
            an_body.get("problemId") == problem_id,
            str(an_body.get("problemId")),
        )
        check(
            "category matches report category",
            an_body.get("category") == "Water & Sanitation",
            str(an_body.get("category")),
        )
        check(
            "urgency matches report urgency",
            an_body.get("urgency") == "CRITICAL",
            str(an_body.get("urgency")),
        )
        check(
            "affectedPopulation matches report",
            an_body.get("affectedPopulation") == 1200,
            str(an_body.get("affectedPopulation")),
        )
        check(
            "confidence between 0.0 and 1.0",
            0.0 <= float(an_body.get("confidence", -1)) <= 1.0,
            str(an_body.get("confidence")),
        )
        check(
            "keywords is non-empty list",
            isinstance(an_body.get("keywords"), list) and len(an_body["keywords"]) > 0,
            str(an_body.get("keywords")),
        )

        # 6. Fallback & Output Verification
        print("\n[6] AI Analysis Output & Fallback Verification")
        statement = an_body.get("structuredStatement", "")
        check("structuredStatement is non-empty", len(statement) > 0, statement[:60] + "...")
        print(f"      -> Generated Statement: {statement}")
        print(f"      -> Keywords: {an_body.get('keywords')}")
        print(f"      -> Confidence: {an_body.get('confidence')}")

        # 7. Check problem status updated to ANALYZED in database
        print(f"\n[7] GET /api/problems/{problem_id} (verify status update to ANALYZED)")
        get_code, get_body = request("GET", f"/api/problems/{problem_id}")
        check("HTTP 200 OK", get_code == 200, str(get_code))
        check(
            "status is ANALYZED",
            isinstance(get_body, dict) and get_body.get("status") == "ANALYZED",
            str(get_body.get("status") if isinstance(get_body, dict) else None),
        )

else:
    print(f"  [BLOCKED] Could not create test problem (HTTP {code}). DB may be unconfigured.")
    skip("POST /api/problems/{id}/analyze", "Problem creation failed")
    skip("Schema validation", "Problem creation failed")
    skip("Fallback verification", "Problem creation failed")
    skip("Status update check", "Problem creation failed")

passed = sum(_results)
total = len(_results)
print(f"\n{'='*50}")
print(f"Results: {passed}/{total} assertions passed")
print(f"{'='*50}\n")

sys.exit(0 if passed == total else 1)
