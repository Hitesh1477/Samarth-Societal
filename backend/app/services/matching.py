"""
Solver Matching Engine — modular matching service for SAMARTH.

Calculates a deterministic 100-point matching score across 6 sub-factors:
- Expertise / Skills:       40 points max
- Category Match:           20 points max
- Location Match:           15 points max
- Capacity:                 10 points max
- Equipment / Resources:     5 points max
- Previous Projects:        10 points max

Generates explainable, evidence-based reasons using actual solver data.
Sorts by matchScore descending and returns top-5 matches.
"""

import uuid
from typing import Optional
from fastapi import HTTPException, status

from app.core.database import get_supabase_admin_client
from app.schemas.enums import SolverType
from app.schemas.matching import SolverProfileSchema, SolverMatchSchema
from app.services import problems as problem_service


# ── Built-in Seed Solvers (Fallback if DB solver_profiles is unpopulated) ─────

SEED_SOLVER_PROFILES: list[SolverProfileSchema] = [
    SolverProfileSchema(
        id="s1-xyz-tech",
        name="XYZ Institute of Technology",
        type=SolverType.UNIVERSITY,
        department="Civil Engineering + GIS Lab",
        district="Ranchi",
        state="Jharkhand",
        categories=["Infrastructure", "Water & Sanitation", "Transport", "Public Safety"],
        expertise=["Civil Engineering", "GIS Mapping", "Drainage Modelling", "Hydrology", "Urban Infrastructure"],
        capacity="HIGH",
        equipment=["GIS Lab", "Drone Surveying Unit", "Hydraulic Modelling Suite"],
        previous_projects=["Urban Waterlogging Mitigation", "Smart Drainage Survey", "Road Elevation Pilot"],
        description="Recommended because this team has experience in drainage modelling, GIS mapping and urban infrastructure projects.",
    ),
    SolverProfileSchema(
        id="s2-bit-mesra",
        name="BIT Mesra",
        type=SolverType.UNIVERSITY,
        department="Environmental Engineering",
        district="Ranchi",
        state="Jharkhand",
        categories=["Environment", "Water & Sanitation", "Infrastructure"],
        expertise=["Environmental Engineering", "Hydrology Research", "Water Quality Analysis", "Urban Planning"],
        capacity="HIGH",
        equipment=["Water Quality Testing Lab", "Soil Mechanics Lab"],
        previous_projects=["River Basin Hydrology Study", "Urban Effluent Management"],
        description="Strong background in hydrology and environmental engineering with urban project experience.",
    ),
    SolverProfileSchema(
        id="s3-ranchi-univ",
        name="Ranchi University",
        type=SolverType.UNIVERSITY,
        department="Geography & Urban Planning",
        district="Ranchi",
        state="Jharkhand",
        categories=["Infrastructure", "Public Safety", "Education", "Transport"],
        expertise=["Urban Planning", "GIS Capability", "Local Geographic Surveying", "Community Resilience"],
        capacity="MEDIUM",
        equipment=["GIS Mapping Workstations"],
        previous_projects=["District Master Plan Assessment", "School Safety Audits"],
        description="Local university with urban planning expertise and strong community connections.",
    ),
    SolverProfileSchema(
        id="s4-abc-infra",
        name="ABC Infrastructure Solutions",
        type=SolverType.INDUSTRY,
        department="Infrastructure & Works Division",
        district="Ranchi",
        state="Jharkhand",
        categories=["Infrastructure", "Transport", "Waste Management"],
        expertise=["Drainage Infrastructure", "Road Construction", "Civic Engineering", "Stormwater Systems"],
        capacity="HIGH",
        equipment=["Heavy Earthmoving Machinery", "Concrete Paving Equipment", "Pipelining Gear"],
        previous_projects=["City Highway Drainage Upgrade", "Urban Culvert Construction"],
        description="Industry partner with proven experience in drainage infrastructure and road elevation projects.",
    ),
    SolverProfileSchema(
        id="s5-iit-dhanbad",
        name="IIT (ISM) Dhanbad",
        type=SolverType.UNIVERSITY,
        department="Environmental Science & Engineering",
        district="Dhanbad",
        state="Jharkhand",
        categories=["Environment", "Water & Sanitation", "Infrastructure", "Agriculture"],
        expertise=["Air Quality Monitoring", "Industrial Waste Treatment", "Water Purification", "Environmental Sensing"],
        capacity="HIGH",
        equipment=["Advanced Air Monitoring Station", "Water Spectrophotometry Lab"],
        previous_projects=["Mine Effluent Purification", "Industrial Air Pollution Audit"],
        description="Premier technical institution with specialized capabilities in environmental monitoring and water treatment.",
    ),
]


# ── Scoring Engine Logic ──────────────────────────────────────────────────────

def calculate_solver_match(
    challenge_category: str,
    challenge_subcategory: str,
    challenge_district: str,
    challenge_text: str,
    solver: SolverProfileSchema,
) -> tuple[float, list[str]]:
    """
    Calculate 100-point deterministic match score and explainable reasons for a solver.
    """
    reasons: list[str] = []
    text_lower = f"{challenge_category} {challenge_subcategory} {challenge_text}".lower()

    # 1. Expertise / Skills (Max 40 points)
    if solver.expertise:
        matched_skills = []
        for skill in solver.expertise:
            skill_words = [w.lower() for w in skill.split() if len(w) > 2]
            if any(word in text_lower for word in skill_words):
                matched_skills.append(skill)

        if matched_skills:
            # Scale overlap: 25 base points + up to 15 points based on overlap ratio
            ratio = len(matched_skills) / max(1, len(solver.expertise))
            exp_pts = round(25.0 + (ratio * 15.0), 1)
            for skill in matched_skills[:3]:
                reasons.append(f"{skill} Expertise" if "expertise" not in skill.lower() else skill)
        else:
            exp_pts = 15.0
    else:
        # Neutral score if expertise data is unavailable
        exp_pts = 20.0

    exp_pts = min(exp_pts, 40.0)

    # 2. Category Match (Max 20 points)
    cat_match = False
    if solver.categories:
        if any(c.lower() == challenge_category.lower() for c in solver.categories):
            cat_pts = 20.0
            cat_match = True
            reasons.append(f"Matches {challenge_category} category")
        elif any(c.lower() in text_lower for c in solver.categories):
            cat_pts = 12.0
            reasons.append("Related domain capability")
        else:
            cat_pts = 0.0
    else:
        cat_pts = 10.0  # neutral

    # 3. Location Match (Max 15 points)
    if solver.district:
        if challenge_district and solver.district.lower() == challenge_district.lower():
            loc_pts = 15.0
            reasons.append(f"Local presence in {solver.district}")
        elif solver.state and "jharkhand" in solver.state.lower():
            loc_pts = 10.0
            reasons.append("Regional state presence")
        else:
            loc_pts = 5.0
    else:
        loc_pts = 7.5  # neutral

    # 4. Capacity (Max 10 points)
    cap = solver.capacity.upper() if solver.capacity else ""
    if cap == "HIGH":
        cap_pts = 10.0
        reasons.append("Available Team Capacity")
    elif cap == "MEDIUM":
        cap_pts = 6.0
    elif cap == "LOW":
        cap_pts = 3.0
    else:
        cap_pts = 5.0  # neutral

    # 5. Equipment / Resources (Max 5 points)
    if solver.equipment:
        matched_equip = [eq for eq in solver.equipment if any(w in text_lower for w in eq.lower().split())]
        if matched_equip:
            eq_pts = 5.0
            reasons.append(f"Equipped with {matched_equip[0]}")
        else:
            eq_pts = 3.0
    else:
        eq_pts = 2.5  # neutral

    # 6. Previous Projects (Max 10 points)
    if solver.previous_projects:
        matched_proj = [p for p in solver.previous_projects if any(w in text_lower for w in p.lower().split())]
        if matched_proj:
            proj_pts = 10.0
            reasons.append("Previous Similar Projects")
        else:
            proj_pts = 5.0
            reasons.append("Past Project Experience")
    else:
        proj_pts = 5.0  # neutral

    # Sum total score (0 to 100)
    total_score = round(exp_pts + cat_pts + loc_pts + cap_pts + eq_pts + proj_pts, 1)
    total_score = min(max(total_score, 0.0), 100.0)

    # Deduplicate reasons while preserving order
    deduped_reasons: list[str] = []
    for r in reasons:
        if r not in deduped_reasons:
            deduped_reasons.append(r)

    # Ensure at least one valid reason is present
    if not deduped_reasons:
        deduped_reasons.append("General Solver Capability Match")

    return total_score, deduped_reasons


# ── Database & Retrieval ──────────────────────────────────────────────────────

async def _fetch_solver_profiles_from_db() -> list[SolverProfileSchema]:
    """Fetch solver profiles from Supabase solver_profiles table, fallback to seed if empty."""
    client = get_supabase_admin_client()
    try:
        res = client.table("solver_profiles").select("*").execute()
        if res.data:
            profiles = []
            for row in res.data:
                profiles.append(
                    SolverProfileSchema(
                        id=str(row["id"]),
                        name=row.get("name", "Unknown Solver"),
                        type=SolverType(row.get("type", "university")),
                        department=row.get("department"),
                        district=row.get("district", ""),
                        state=row.get("state", ""),
                        categories=row.get("categories", []),
                        expertise=row.get("expertise", []),
                        capacity=row.get("capacity", "HIGH"),
                        equipment=row.get("equipment", []),
                        previous_projects=row.get("previous_projects", []),
                        description=row.get("description", ""),
                    )
                )
            return profiles
    except Exception as exc:
        print(f"[INFO] solver_profiles DB fetch notice: {exc}. Using fallback solver dataset.")

    return SEED_SOLVER_PROFILES


async def get_solver_matches_for_challenge(challenge_id: str) -> list[SolverMatchSchema]:
    """
    Get top-5 solver matches for a challenge or problem ID.
    Raises 404 if challenge_id is not found in DB or mock list.
    """
    client = get_supabase_admin_client()
    challenge_category = "Infrastructure"
    challenge_subcategory = ""
    challenge_district = ""
    challenge_text = ""
    found = False

    # 1. Try querying challenges table
    try:
        res = client.table("challenges").select("*").eq("id", challenge_id).limit(1).execute()
        if res.data:
            c = res.data[0]
            challenge_category = c.get("category", "Infrastructure")
            challenge_subcategory = c.get("subcategory", "")
            challenge_district = c.get("district", "")
            challenge_text = f"{c.get('title', '')} {c.get('description', '')}"
            found = True
    except Exception:
        pass

    # 2. If not found in challenges, check problems table
    if not found:
        try:
            p = await problem_service.get_problem(challenge_id)
            challenge_category = p.category
            challenge_subcategory = p.subcategory
            challenge_district = p.location.district
            challenge_text = f"{p.title} {p.description}"
            found = True
        except HTTPException:
            pass

    # 3. If still not found, check mock hardcoded challenge IDs for dev compatibility (e.g. ch-001)
    if not found and challenge_id.startswith("ch-"):
        found = True
        challenge_category = "Infrastructure"
        challenge_subcategory = "Drainage / Road Accessibility"
        challenge_district = "Ranchi"
        challenge_text = "Urban Road Waterlogging Ranchi Heavy rainfall causes severe waterlogging"

    if not found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Challenge '{challenge_id}' not found.",
        )

    # Fetch solver candidates
    solvers = await _fetch_solver_profiles_from_db()

    # Calculate match score and reasons for each candidate
    matched_results: list[SolverMatchSchema] = []
    for solver in solvers:
        score, reasons = calculate_solver_match(
            challenge_category=challenge_category,
            challenge_subcategory=challenge_subcategory,
            challenge_district=challenge_district,
            challenge_text=challenge_text,
            solver=solver,
        )
        matched_results.append(
            SolverMatchSchema(
                id=solver.id,
                name=solver.name,
                type=solver.type,
                department=solver.department,
                match_score=score,
                reasons=reasons,
                description=solver.description,
            )
        )

    # Sort by matchScore descending and take top 5
    matched_results.sort(key=lambda s: s.match_score, reverse=True)
    return matched_results[:5]
