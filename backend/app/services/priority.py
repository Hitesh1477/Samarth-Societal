"""
Priority Scoring Engine — calculates deterministic and explainable priority scores.

Factors & Allocations:
- Safety Risk: max 30 points
- Population Impact: max 25 points
- Recurrence / Clustered Reports: max 20 points
- Evidence Quality: max 15 points
- Location Criticality: max 10 points
----------------------------------------
Total Score: max 100 points
Level: HIGH (>= 70), MEDIUM (40 - 69), LOW (< 40)
"""

from typing import Optional
from fastapi import HTTPException, status

from app.core.database import get_supabase_admin_client
from app.schemas.enums import PriorityLevel, UrgencyLevel
from app.schemas.priority import (
    PriorityBreakdownSchema,
    PriorityScoreSchema,
    ScoreFactorSchema,
)
from app.services import problems as problem_service


# ── Factor Calculations ────────────────────────────────────────────────────────

def calculate_safety_risk(urgency: str, title: str, description: str) -> float:
    """Calculate safety risk factor (max 30 points)."""
    urg = str(urgency).upper()
    if urg == UrgencyLevel.CRITICAL:
        base = 27.0
    elif urg == UrgencyLevel.HIGH:
        base = 20.0
    elif urg == UrgencyLevel.MEDIUM:
        base = 12.0
    else:
        base = 5.0

    # Boost if explicit hazard terms found
    hazard_terms = {
        "hazard", "danger", "contamination", "accident", "fire",
        "collapse", "severe", "life-threatening", "injury", "poison", "toxic"
    }
    text = f"{title} {description}".lower()
    boost = 3.0 if any(term in text for term in hazard_terms) else 0.0

    return min(base + boost, 30.0)


def calculate_population_impact(affected_pop: int) -> float:
    """Calculate population impact factor (max 25 points)."""
    pop = max(0, affected_pop)
    if pop >= 5000:
        return 25.0
    elif pop >= 2000:
        return 20.0
    elif pop >= 1000:
        return 15.0
    elif pop >= 500:
        return 10.0
    elif pop >= 100:
        return 5.0
    else:
        return 2.0


def calculate_recurrence(report_count: int) -> float:
    """Calculate recurrence / report frequency factor (max 20 points)."""
    count = max(1, report_count)
    if count >= 10:
        return 20.0
    elif count >= 5:
        return 16.0
    elif count >= 3:
        return 12.0
    elif count == 2:
        return 8.0
    else:
        return 4.0


def calculate_evidence(evidence_count: int) -> float:
    """Calculate evidence quality factor (max 15 points)."""
    count = max(0, evidence_count)
    if count >= 3:
        return 15.0
    elif count == 2:
        return 11.0
    elif count == 1:
        return 7.0
    else:
        return 3.0


def calculate_location_risk(location_name: str, district: str, title: str, description: str) -> float:
    """Calculate location risk / facility proximity factor (max 10 points)."""
    critical_facilities = {
        "hospital", "school", "highway", "nh-", "station", "market",
        "college", "bridge", "clinic", "phc", "water plant", "dispensary"
    }
    combined_text = f"{location_name} {district} {title} {description}".lower()
    return 10.0 if any(fac in combined_text for fac in critical_facilities) else 4.0


def determine_priority_level(total: float) -> PriorityLevel:
    """Determine PriorityLevel based on total score."""
    if total >= 70.0:
        return PriorityLevel.HIGH
    elif total >= 40.0:
        return PriorityLevel.MEDIUM
    else:
        return PriorityLevel.LOW


def generate_explanation(
    total: float,
    level: PriorityLevel,
    safety: float,
    pop: float,
    affected_pop: int,
    rec: float,
    report_count: int,
    ev: float,
    loc: float,
) -> str:
    """Generate human-readable explainable rationale."""
    reasons = []
    if safety >= 20.0:
        reasons.append(f"high safety risk ({int(safety)}/30)")
    if pop >= 15.0:
        reasons.append(f"significant population impact ({int(pop)}/25 affecting {affected_pop:,} citizens)")
    if rec >= 12.0:
        reasons.append(f"multiple recurring reports ({report_count} reports)")
    if ev >= 11.0:
        reasons.append("verified media evidence attached")
    if loc >= 10.0:
        reasons.append("proximity to critical public facilities")

    reason_str = ", ".join(reasons) if reasons else "baseline severity metrics"
    return f"{level.value} Priority ({int(round(total))}/100): Key factors include {reason_str}."


# ── Core Service Functions ───────────────────────────────────────────────────

def build_priority_score(
    target_id: str,
    title: str,
    description: str,
    urgency: str,
    affected_population: int,
    report_count: int,
    evidence_count: int,
    location_name: str,
    district: str,
) -> PriorityScoreSchema:
    """Build and compute deterministic PriorityScoreSchema."""
    safety_pts = calculate_safety_risk(urgency, title, description)
    pop_pts = calculate_population_impact(affected_population)
    rec_pts = calculate_recurrence(report_count)
    ev_pts = calculate_evidence(evidence_count)
    loc_pts = calculate_location_risk(location_name, district, title, description)

    total_score = round(safety_pts + pop_pts + rec_pts + ev_pts + loc_pts, 1)
    level = determine_priority_level(total_score)

    explanation = generate_explanation(
        total_score, level, safety_pts, pop_pts, affected_population,
        rec_pts, report_count, ev_pts, loc_pts
    )

    breakdown = PriorityBreakdownSchema(
        safety_risk=ScoreFactorSchema(score=safety_pts, max=30.0),
        population_impact=ScoreFactorSchema(score=pop_pts, max=25.0),
        recurrence=ScoreFactorSchema(score=rec_pts, max=20.0),
        evidence=ScoreFactorSchema(score=ev_pts, max=15.0),
        location_risk=ScoreFactorSchema(score=loc_pts, max=10.0),
    )

    return PriorityScoreSchema(
        challenge_id=target_id,
        total=total_score,
        level=level,
        breakdown=breakdown,
        explanation=explanation,
    )


async def get_priority_for_challenge(challenge_id: str) -> PriorityScoreSchema:
    """
    Compute PriorityScore for a challenge or problem ID.
    Raises 404 if ID does not exist in challenges or problems.
    """
    client = get_supabase_admin_client()

    # 1. First check if challenge_id exists in challenges table
    try:
        c_res = client.table("challenges").select("*").eq("id", challenge_id).limit(1).execute()
        if c_res.data:
            c = c_res.data[0]
            return build_priority_score(
                target_id=challenge_id,
                title=c.get("title", "Challenge"),
                description=c.get("description", ""),
                urgency="HIGH",
                affected_population=c.get("affected_population", 1000),
                report_count=c.get("report_count", 1),
                evidence_count=2,
                location_name=c.get("location_name", ""),
                district=c.get("district", ""),
            )
    except Exception:
        pass

    # 2. Fall back to problems table if challenge_id is a problem_id
    try:
        problem = await problem_service.get_problem(challenge_id)
        return build_priority_score(
            target_id=problem.id,
            title=problem.title,
            description=problem.description,
            urgency=problem.urgency,
            affected_population=problem.affected_population,
            report_count=1,
            evidence_count=len(problem.evidence),
            location_name=problem.location.name,
            district=problem.location.district,
        )
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Challenge or Problem '{challenge_id}' not found.",
        )
