"""
AI Provider abstraction for SAMARTH problem analysis.

Provides integration with OpenAI when OPENAI_API_KEY is configured,
with seamless deterministic fallback when unconfigured or offline.
"""

import json
import re
import httpx
from typing import Optional

from app.core.config import settings
from app.schemas.ai import AIAnalysisSchema
from app.schemas.problems import ProblemReportSchema
from app.schemas.enums import ProblemCategory, UrgencyLevel


def extract_fallback_keywords(title: str, description: str) -> list[str]:
    """Extract 3-6 distinct keywords from title and description."""
    stopwords = {
        "the", "and", "a", "an", "in", "on", "at", "for", "to", "of",
        "with", "by", "is", "are", "was", "were", "near", "causing",
        "daily", "very", "this", "that", "from", "have", "been", "has"
    }
    words = re.findall(r"[a-zA-Z0-9]+", f"{title} {description}")
    clean_words: list[str] = []
    seen: set[str] = set()

    for w in words:
        w_lower = w.lower()
        if len(w_lower) >= 4 and w_lower not in stopwords and w_lower not in seen:
            seen.add(w_lower)
            clean_words.append(w.capitalize())
            if len(clean_words) >= 5:
                break

    if not clean_words:
        clean_words = ["Report", "Issue", "Community"]

    return clean_words


def generate_fallback_analysis(problem: ProblemReportSchema) -> AIAnalysisSchema:
    """Generate deterministic fallback analysis for local testing/offline use."""
    subcat = problem.subcategory if problem.subcategory else "General"
    statement = f"Structured Analysis: {problem.title} — {problem.description}"

    return AIAnalysisSchema(
        problem_id=problem.id,
        structured_statement=statement,
        category=problem.category,
        subcategory=subcat,
        keywords=extract_fallback_keywords(problem.title, problem.description),
        urgency=problem.urgency,
        confidence=0.85,
        affected_population=problem.affected_population,
        evidence_count=len(problem.evidence),
    )


async def analyze_problem_with_openai(problem: ProblemReportSchema) -> AIAnalysisSchema:
    """Analyze problem report using OpenAI Chat Completions API."""
    api_key = settings.OPENAI_API_KEY.strip()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    prompt = (
        f"Analyze the following citizen problem report:\n"
        f"Title: {problem.title}\n"
        f"Description: {problem.description}\n"
        f"Category: {problem.category}\n"
        f"Subcategory: {problem.subcategory}\n"
        f"Urgency: {problem.urgency}\n"
        f"Affected Population: {problem.affected_population}\n"
        f"District: {problem.location.district}\n"
        f"Evidence Count: {len(problem.evidence)}\n\n"
        f"Return ONLY a JSON object with fields:\n"
        f"- structuredStatement: concise formal problem statement framing core issue and impact\n"
        f"- category: valid ProblemCategory string\n"
        f"- subcategory: refined subcategory string\n"
        f"- keywords: array of 3 to 6 key terms\n"
        f"- urgency: one of 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'\n"
        f"- confidence: float score between 0.0 and 1.0\n"
        f"- affectedPopulation: integer\n"
    )

    payload = {
        "model": "gpt-4o-mini",
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": "You are an expert civic issue analyst for SAMARTH platform. Produce valid JSON analysis matching requested schema."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)

    return AIAnalysisSchema(
        problem_id=problem.id,
        structured_statement=parsed.get("structuredStatement") or f"Analysis for: {problem.title}",
        category=parsed.get("category") or problem.category,
        subcategory=parsed.get("subcategory") or problem.subcategory or "General",
        keywords=parsed.get("keywords") or extract_fallback_keywords(problem.title, problem.description),
        urgency=parsed.get("urgency") or problem.urgency,
        confidence=float(parsed.get("confidence", 0.9)),
        affected_population=int(parsed.get("affectedPopulation", problem.affected_population)),
        evidence_count=len(problem.evidence),
    )


async def analyze_problem_with_ai(
    problem: ProblemReportSchema,
    force_fallback: bool = False,
) -> AIAnalysisSchema:
    """
    Main entry point for AI problem analysis.
    Uses OpenAI if OPENAI_API_KEY is configured, otherwise uses fallback.
    """
    api_key = settings.OPENAI_API_KEY.strip() if settings.OPENAI_API_KEY else ""

    if force_fallback or not api_key:
        return generate_fallback_analysis(problem)

    try:
        return await analyze_problem_with_openai(problem)
    except Exception as exc:
        print(f"[AI PROVIDER WARN] OpenAI API call failed ({exc}). Falling back to deterministic analysis.")
        return generate_fallback_analysis(problem)
