"""
Stage 3C test suite — run from backend/ directory:
    python test_stage3c.py

Covers:
  - OpenAPI route registration for GET /api/challenges/{challenge_id}/priority
  - Priority calculation for HIGH priority problem report
  - Priority calculation for LOW/MEDIUM priority problem report
  - Field name & CamelCase contract validation (challengeId, total, level, breakdown, explanation)
  - Sub-factor breakdown validation (safetyRisk, populationImpact, recurrence, evidence, locationRisk)
  - Mathematical score consistency (sum of breakdown scores == total score)
  - Nonexistent problem / challenge ID returns 404
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


print("\n=== Stage 3C Test Suite: Priority Scoring Engine ===\n")

# 1. OpenAPI Route Registration
print("[1] GET /openapi.json  (route registration)")
code, body = request("GET", "/openapi.json")
paths = body.get("paths", {}) if isinstance(body, dict) else {}
check("OpenAPI reachable", code == 200, str(code))
check(
    "GET /api/challenges/{challenge_id}/priority registered",
    "/api/challenges/{challenge_id}/priority" in paths,
)
check(
    "GET /api/problems/{problem_id}/priority registered",
    "/api/problems/{problem_id}/priority" in paths,
)

# 2. Nonexistent Challenge / Problem (Expect 404)
print("\n[2] GET /api/challenges/00000000-0000-0000-0000-000000000000/priority (expect 404)")
code, body = request("GET", "/api/challenges/00000000-0000-0000-0000-000000000000/priority")
check("HTTP 404", code == 404, str(code))
check("has detail field", isinstance(body, dict) and "detail" in body, str(body))

# 3. Create High Priority Problem Report
print("\n[3] Creating Test Problem Reports (High & Low Severity)")

HIGH_PAYLOAD = {
    "title": "Bridge Collapse Hazard near District Hospital",
    "description": "Major structural cracks on hospital access bridge causing critical accident hazard for 6,000 daily commuters",
    "category": "Infrastructure",
    "subcategory": "Bridges & Roads",
    "urgency": "CRITICAL",
    "affectedPopulation": 6000,
    "location": {"lat": 19.0760, "lng": 72.8777, "name": "Hospital Bridge", "district": "Mumbai"},
    "evidence": [
        {"id": "ev1", "type": "image", "url": "http://example.com/crack1.jpg", "name": "crack1.jpg"},
        {"id": "ev2", "type": "image", "url": "http://example.com/crack2.jpg", "name": "crack2.jpg"},
    ],
    "reporterName": "Dr. Anish Sharma",
}

LOW_PAYLOAD = {
    "title": "Faded Street Signboard",
    "description": "Street name sign board paint is faded near park corner",
    "category": "Other",
    "subcategory": "Signage",
    "urgency": "LOW",
    "affectedPopulation": 30,
    "location": {"lat": 18.5204, "lng": 73.8567, "name": "Park Corner", "district": "Pune"},
    "evidence": [],
    "reporterName": "Sunil V",
}

code_h, res_h = request("POST", "/api/problems", HIGH_PAYLOAD)
code_l, res_l = request("POST", "/api/problems", LOW_PAYLOAD)

high_id = res_h.get("id") if isinstance(res_h, dict) else None
low_id = res_l.get("id") if isinstance(res_l, dict) else None

if code_h == 201 and high_id and code_l == 201 and low_id:
    check("High severity problem created", True, f"ID: {high_id}")
    check("Low severity problem created", True, f"ID: {low_id}")

    # 4. Priority Calculation for High Severity Problem
    print(f"\n[4] GET /api/challenges/{high_id}/priority (High Severity Problem)")
    p_code, p_body = request("GET", f"/api/challenges/{high_id}/priority")
    check("HTTP 200 OK", p_code == 200, str(p_code))

    if p_code == 200 and isinstance(p_body, dict):
        # 5. Field & Schema Validation
        print("\n[5] Response Schema & CamelCase Field Validation")
        required_fields = [
            ("challengeId", str),
            ("total", (int, float)),
            ("level", str),
            ("breakdown", dict),
            ("explanation", str),
        ]
        for fname, ftype in required_fields:
            val = p_body.get(fname)
            check(
                f"field '{fname}' present and valid type ({ftype})",
                fname in p_body and isinstance(val, ftype),
                f"val={val!r}",
            )

        check("level is HIGH", p_body.get("level") == "HIGH", str(p_body.get("level")))
        check("total score >= 70.0", float(p_body.get("total", 0)) >= 70.0, str(p_body.get("total")))

        # 6. Breakdown Sub-Factors Validation
        print("\n[6] Breakdown Sub-Factor Allocations & Sum Validation")
        breakdown = p_body.get("breakdown", {})
        factors = ["safetyRisk", "populationImpact", "recurrence", "evidence", "locationRisk"]

        sum_scores = 0.0
        for factor_name in factors:
            sub = breakdown.get(factor_name)
            is_valid_sub = isinstance(sub, dict) and "score" in sub and "max" in sub
            check(f"breakdown factor '{factor_name}' valid", is_valid_sub, str(sub))
            if is_valid_sub:
                score = float(sub["score"])
                max_score = float(sub["max"])
                check(f"'{factor_name}' 0 <= score <= max", 0.0 <= score <= max_score, f"{score}/{max_score}")
                sum_scores += score

        total = float(p_body.get("total", 0))
        check("sum of breakdown scores matches total score", round(sum_scores, 1) == round(total, 1), f"sum={sum_scores:.1f}, total={total:.1f}")
        check("explanation contains non-empty text", len(p_body.get("explanation", "")) > 10, p_body.get("explanation"))

    # 7. Priority Calculation for Low Severity Problem
    print(f"\n[7] GET /api/problems/{low_id}/priority (Low Severity Problem)")
    low_code, low_body = request("GET", f"/api/problems/{low_id}/priority")
    check("HTTP 200 OK", low_code == 200, str(low_code))
    if low_code == 200 and isinstance(low_body, dict):
        check("level is LOW or MEDIUM", low_body.get("level") in ("LOW", "MEDIUM"), str(low_body.get("level")))
        check("total score < 70.0", float(low_body.get("total", 100)) < 70.0, str(low_body.get("total")))

else:
    print("  [BLOCKED] Could not create test problems in DB.")
    skip("GET /api/challenges/{id}/priority", "Problem creation failed")
    skip("Breakdown validation", "Problem creation failed")

passed = sum(_results)
total = len(_results)
print(f"\n{'='*50}")
print(f"Results: {passed}/{total} assertions passed")
print(f"{'='*50}\n")

sys.exit(0 if passed == total else 1)
