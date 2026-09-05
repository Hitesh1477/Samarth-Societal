"""
Duplicate detection service — semantic similarity & clustering for problem reports.

Supports OpenAI embedding similarity when OPENAI_API_KEY is configured,
with full deterministic fallback using token overlap + category + geographic proximity.
"""

import math
import re
import uuid
from datetime import datetime, timezone
from typing import Optional, List

import httpx
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.database import get_supabase_admin_client
from app.schemas.duplicates import DuplicateClusterSchema, DuplicateReportSchema
from app.schemas.problems import ProblemReportSchema
from app.services import problems as problem_service


# ── Distance & Geographic Helpers ─────────────────────────────────────────────

def calculate_haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate geographic distance in kilometers between two lat/lng coordinates."""
    if lat1 == 0 and lng1 == 0 and lat2 == 0 and lng2 == 0:
        return 0.0
    R = 6371.0  # Earth's radius in km
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def format_distance(dist_km: float) -> str:
    """Format distance in meters or kilometers."""
    if dist_km < 1.0:
        meters = int(round(dist_km * 1000))
        return f"{meters} m"
    return f"{round(dist_km, 1)} km"


# ── Deterministic Similarity Calculation ──────────────────────────────────────

def compute_text_tokens(text: str) -> set[str]:
    """Extract clean lowercase tokens from text excluding common stopwords."""
    stopwords = {
        "the", "and", "a", "an", "in", "on", "at", "for", "to", "of",
        "with", "by", "is", "are", "was", "were", "near", "causing",
        "daily", "very", "this", "that", "from", "have", "been", "has",
        "near", "there", "their", "where", "which", "some", "more"
    }
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return {w for w in words if len(w) >= 3 and w not in stopwords}


def compute_deterministic_similarity(
    p1: ProblemReportSchema,
    p2: ProblemReportSchema,
) -> float:
    """
    Calculate deterministic similarity score in range [0.0, 1.0].
    Combines text Jaccard overlap, category/subcategory match, and geo proximity.
    """
    # 1. Text token overlap
    tokens1 = compute_text_tokens(f"{p1.title} {p1.description}")
    tokens2 = compute_text_tokens(f"{p2.title} {p2.description}")

    if not tokens1 or not tokens2:
        jaccard = 0.0
    else:
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        jaccard = len(intersection) / len(union) if union else 0.0

    # 2. Category & Subcategory score
    cat_score = 0.0
    if p1.category == p2.category:
        cat_score = 0.7
        if p1.subcategory and p2.subcategory and p1.subcategory.lower() == p2.subcategory.lower():
            cat_score = 1.0

    # 3. Location proximity score
    dist_km = calculate_haversine_distance(
        p1.location.lat, p1.location.lng,
        p2.location.lat, p2.location.lng,
    )
    if dist_km <= 1.0:
        loc_score = 1.0
    elif dist_km <= 5.0:
        loc_score = 0.8
    elif dist_km <= 20.0:
        loc_score = 0.5
    elif p1.location.district and p2.location.district and p1.location.district.lower() == p2.location.district.lower():
        loc_score = 0.4
    else:
        loc_score = 0.0

    # Weighted similarity combination
    sim = (0.50 * jaccard) + (0.30 * cat_score) + (0.20 * loc_score)

    # Boost if text overlap and category match strongly
    if jaccard >= 0.35 and cat_score >= 0.7:
        sim = max(sim, 0.88)
    elif jaccard >= 0.20 and cat_score >= 0.7:
        sim = max(sim, 0.75)

    return round(min(max(sim, 0.0), 1.0), 2)


# ── OpenAI Embedding Similarity Calculation ───────────────────────────────────

async def fetch_openai_embedding(text: str) -> Optional[List[float]]:
    """Fetch text embedding from OpenAI embedding API."""
    api_key = settings.OPENAI_API_KEY.strip()
    if not api_key:
        return None

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"input": text, "model": "text-embedding-3-small"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post("https://api.openai.com/v1/embeddings", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["data"][0]["embedding"]
    except Exception as exc:
        print(f"[WARN] OpenAI embedding fetch failed: {exc}")
        return None


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vector floats."""
    dot = sum(a * b for a, b in zip(vec1, vec2))
    mag1 = math.sqrt(sum(a * a for a in vec1))
    mag2 = math.sqrt(sum(b * b for b in vec2))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return round(min(max(dot / (mag1 * mag2), 0.0), 1.0), 2)


# ── Core Service Function ─────────────────────────────────────────────────────

async def get_duplicate_cluster(problem_id: str) -> DuplicateClusterSchema:
    """
    Fetch duplicates for problem_id, persist clusters to Supabase,
    and return DuplicateClusterSchema matching frontend API contract.
    """
    # 1. Fetch target problem (raises 404 if non-existent)
    target = await problem_service.get_problem(problem_id)

    # 2. Fetch all existing problems from database
    all_problems = await problem_service.list_problems()

    # Exclude target problem itself
    candidates = [p for p in all_problems if p.id != target.id]

    duplicate_reports: List[DuplicateReportSchema] = []
    cluster_pairs: List[tuple[str, float]] = []

    # 3. Try OpenAI embedding mode if key configured
    use_openai = bool(settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip())
    target_emb = None
    if use_openai:
        target_text = f"{target.title}. {target.category} ({target.subcategory}). {target.description}"
        target_emb = await fetch_openai_embedding(target_text)

    for cand in candidates:
        dist_km = calculate_haversine_distance(
            target.location.lat, target.location.lng,
            cand.location.lat, cand.location.lng,
        )
        dist_str = format_distance(dist_km)

        sim_score = 0.0
        if target_emb:
            cand_text = f"{cand.title}. {cand.category} ({cand.subcategory}). {cand.description}"
            cand_emb = await fetch_openai_embedding(cand_text)
            if cand_emb:
                sim_score = cosine_similarity(target_emb, cand_emb)
            else:
                sim_score = compute_deterministic_similarity(target, cand)
        else:
            sim_score = compute_deterministic_similarity(target, cand)

        # Include candidate if similarity >= 0.50
        if sim_score >= 0.50:
            loc_str = cand.location.name
            if cand.location.district and cand.location.district not in loc_str:
                loc_str = f"{loc_str}, {cand.location.district}" if loc_str else cand.location.district

            rep = DuplicateReportSchema(
                report_id=cand.id,
                title=cand.title,
                similarity=sim_score,
                distance=dist_str,
                date=cand.created_at,
                location=loc_str or "Location",
                reporter=cand.reporter_name or "Anonymous",
            )
            duplicate_reports.append(rep)

            if sim_score >= 0.70:
                cluster_pairs.append((cand.id, sim_score))

    # 4. Sort duplicate reports by similarity descending
    duplicate_reports.sort(key=lambda r: r.similarity, reverse=True)

    # 5. Persist clusters in Supabase problem_clusters table
    if cluster_pairs:
        client = get_supabase_admin_client()
        now_iso = datetime.now(timezone.utc).isoformat()
        for cand_id, sim in cluster_pairs:
            try:
                client.table("problem_clusters").upsert({
                    "primary_problem_id": target.id,
                    "clustered_problem_id": cand_id,
                    "similarity_score": sim,
                    "created_at": now_iso,
                }, on_conflict="primary_problem_id,clustered_problem_id").execute()
            except Exception as exc:
                print(f"[WARN] Failed to persist cluster pair ({target.id}, {cand_id}): {exc}")

    # 6. Construct DuplicateClusterSchema
    top_similarity = duplicate_reports[0].similarity if duplicate_reports else 1.0
    total_count = 1 + len(duplicate_reports)

    return DuplicateClusterSchema(
        problem_id=target.id,
        total_reports=total_count,
        similarity=top_similarity,
        reports=duplicate_reports,
        unified_challenge_id=target.challenge_id,
    )
