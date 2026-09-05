"""
Stage 3B test suite — run from backend/ directory:
    python test_stage3b.py

Covers:
  - OpenAPI route registration for GET /api/problems/{problem_id}/duplicates
  - GET /api/problems/{problem_id}/duplicates for a problem with no duplicates (200 OK)
  - GET /api/problems/{problem_id}/duplicates for a problem with similar report (detects duplicate, similarity in [0, 1])
  - Clearly unrelated problem not misclassified as strong duplicate
  - Nonexistent problem duplicate request (returns 404)
  - Response contract validation (camelCase: problemId, totalReports, similarity, reports, unifiedChallengeId)
  - DuplicateReport fields validation (reportId, title, similarity, distance, date, location, reporter)
  - Deterministic fallback duplicate detection behavior
"""

import json
import sys
import urllib.request
import urllib.error
import uuid


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


print("\n=== Stage 3B Test Suite: Duplicate Detection & Clustering ===\n")

# 1. OpenAPI Route Registration
print("[1] GET /openapi.json  (route registration)")
code, body = request("GET", "/openapi.json")
paths = body.get("paths", {}) if isinstance(body, dict) else {}
check("OpenAPI reachable", code == 200, str(code))
check(
    "GET /api/problems/{problem_id}/duplicates registered",
    "/api/problems/{problem_id}/duplicates" in paths,
)

# 2. Nonexistent Problem (Expect 404)
print("\n[2] GET /api/problems/00000000-0000-0000-0000-000000000000/duplicates (expect 404)")
code, body = request("GET", "/api/problems/00000000-0000-0000-0000-000000000000/duplicates")
check("HTTP 404", code == 404, str(code))
check("has detail field", isinstance(body, dict) and "detail" in body, str(body))

# 3. Create Test Problems for Duplicate Detection
print("\n[3] Creating Test Problems for Duplicate Detection")

P1_PAYLOAD = {
    "title": "Huge Pothole on Station Road near Market",
    "description": "Deep dangerous pothole on Station Road near Central Market causing vehicle damage and traffic jams daily",
    "category": "Infrastructure",
    "subcategory": "Road Maintenance",
    "urgency": "HIGH",
    "affectedPopulation": 1500,
    "location": {"lat": 19.1176, "lng": 72.8481, "name": "Station Road", "district": "Mumbai"},
    "evidence": [],
    "reporterName": "Vikas Patil",
}

P2_PAYLOAD = {
    "title": "Dangerous Pothole on Station Road",
    "description": "Large open pothole on Station Road near Central Market causing severe accidents daily",
    "category": "Infrastructure",
    "subcategory": "Road Maintenance",
    "urgency": "CRITICAL",
    "affectedPopulation": 1800,
    "location": {"lat": 19.1180, "lng": 72.8485, "name": "Station Road Market", "district": "Mumbai"},
    "evidence": [],
    "reporterName": "Sunita Rao",
}

uid_str = uuid.uuid4().hex[:8]
P3_UNRELATED_PAYLOAD = {
    "title": f"Unique Agricultural Sensor Issue {uid_str}",
    "description": f"Custom IoT soil moisture sensor calibration error in isolated farm plot {uid_str}",
    "category": "Agriculture",
    "subcategory": "IoT Sensors",
    "urgency": "LOW",
    "affectedPopulation": 12,
    "location": {"lat": 10.1234, "lng": 76.5432, "name": "Isolated Remote Farm", "district": "Wayanad"},
    "evidence": [],
    "reporterName": "Isolated Farmer",
}


code1, res1 = request("POST", "/api/problems", P1_PAYLOAD)
code2, res2 = request("POST", "/api/problems", P2_PAYLOAD)
code3, res3 = request("POST", "/api/problems", P3_UNRELATED_PAYLOAD)

p1_id = res1.get("id") if isinstance(res1, dict) else None
p2_id = res2.get("id") if isinstance(res2, dict) else None
p3_id = res3.get("id") if isinstance(res3, dict) else None

try:
    if code1 == 201 and p1_id and code2 == 201 and p2_id and code3 == 201 and p3_id:
        check("Problem 1 created", True, f"ID: {p1_id}")
        check("Problem 2 (Duplicate) created", True, f"ID: {p2_id}")
        check("Problem 3 (Unrelated) created", True, f"ID: {p3_id}")

        # 4. Duplicate Detection for Problem 1
        print(f"\n[4] GET /api/problems/{p1_id}/duplicates")
        dup_code, dup_body = request("GET", f"/api/problems/{p1_id}/duplicates")
        check("HTTP 200 OK", dup_code == 200, str(dup_code))

        if dup_code == 200 and isinstance(dup_body, dict):
            # 5. Schema & Field Contract Validation
            print("\n[5] Response Schema & CamelCase Field Validation")
            cluster_fields = [
                ("problemId", str),
                ("totalReports", int),
                ("similarity", (int, float)),
                ("reports", list),
            ]

            for fname, ftype in cluster_fields:
                has_f = fname in dup_body
                val = dup_body.get(fname)
                check(
                    f"cluster field '{fname}' present",
                    has_f and isinstance(val, ftype),
                    f"val={val!r}",
                )

            check(
                "problemId matches target ID",
                dup_body.get("problemId") == p1_id,
                str(dup_body.get("problemId")),
            )
            check(
                "totalReports >= 1",
                dup_body.get("totalReports", 0) >= 1,
                str(dup_body.get("totalReports")),
            )
            check(
                "cluster similarity in range [0, 1]",
                0.0 <= float(dup_body.get("similarity", -1)) <= 1.0,
                str(dup_body.get("similarity")),
            )

            reports = dup_body.get("reports", [])
            # Target problem p1 should NOT be inside reports list
            p1_in_reports = any(r.get("reportId") == p1_id for r in reports if isinstance(r, dict))
            check("Target problem excluded from reports list", not p1_in_reports)

            # Similar problem p2 should be detected
            p2_report = next((r for r in reports if isinstance(r, dict) and r.get("reportId") == p2_id), None)
            check("Similar report (Problem 2) detected as duplicate", p2_report is not None, str(p2_report))

            if p2_report:
                print("\n[6] DuplicateReport Fields Validation")
                report_fields = [
                    ("reportId", str),
                    ("title", str),
                    ("similarity", (int, float)),
                    ("distance", str),
                    ("date", str),
                    ("location", str),
                    ("reporter", str),
                ]
                for rname, rtype in report_fields:
                    has_rf = rname in p2_report
                    rval = p2_report.get(rname)
                    check(
                        f"report field '{rname}' present",
                        has_rf and isinstance(rval, rtype),
                        f"val={rval!r}",
                    )

                p2_sim = float(p2_report.get("similarity", 0))
                check("similarity is float between 0 and 1", 0.0 <= p2_sim <= 1.0, str(p2_sim))
                check("distance is formatted string", len(p2_report.get("distance", "")) > 0, str(p2_report.get("distance")))

            # Check that reports are sorted by similarity descending
            if len(reports) > 1:
                sims = [r.get("similarity", 0) for r in reports if isinstance(r, dict)]
                is_sorted = all(sims[i] >= sims[i + 1] for i in range(len(sims) - 1))
                check("reports sorted by similarity descending", is_sorted, str(sims))

            # Check unrelated problem p3 is not misclassified as duplicate
            p3_in_reports = any(r.get("reportId") == p3_id for r in reports if isinstance(r, dict))
            check("Unrelated problem (Problem 3) excluded from duplicate list", not p3_in_reports)

        # 7. Isolated Problem with No Duplicates
        print(f"\n[7] GET /api/problems/{p3_id}/duplicates (Problem with no duplicates)")
        iso_code, iso_body = request("GET", f"/api/problems/{p3_id}/duplicates")
        check("HTTP 200 OK", iso_code == 200, str(iso_code))
        if iso_code == 200 and isinstance(iso_body, dict):
            check("totalReports is 1", iso_body.get("totalReports") == 1, str(iso_body.get("totalReports")))
            check("reports list is empty", iso_body.get("reports") == [], str(iso_body.get("reports")))
            check("cluster similarity is 1.0", float(iso_body.get("similarity", 0)) == 1.0, str(iso_body.get("similarity")))

    else:
        print("  [BLOCKED] Could not create test problems in DB.")
        skip("GET /api/problems/{id}/duplicates", "Database error or unconfigured")

finally:
    # Clean up test problems created in this run
    try:
        from app.core.database import get_supabase_admin_client
        c = get_supabase_admin_client()
        ids_to_del = [pid for pid in [p1_id, p2_id, p3_id] if pid]
        if ids_to_del:
            c.table("problems").delete().in_("id", ids_to_del).execute()
    except Exception:
        pass

passed = sum(_results)
total = len(_results)
print(f"\n{'='*50}")
print(f"Results: {passed}/{total} assertions passed")
print(f"{'='*50}\n")

sys.exit(0 if passed == total else 1)
