"""AI provider for structured SAMARTH problem analysis."""

import asyncio
import json
import re

from google import genai
from google.genai import types

from app.core.config import settings
from app.schemas.ai import AIAnalysisSchema
from app.schemas.problems import ProblemReportSchema


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

    for word in words:
        word_lower = word.lower()
        if len(word_lower) >= 4 and word_lower not in stopwords and word_lower not in seen:
            seen.add(word_lower)
            clean_words.append(word.capitalize())
            if len(clean_words) >= 5:
                break

    return clean_words or ["Report", "Issue", "Community"]


def generate_fallback_analysis(problem: ProblemReportSchema) -> AIAnalysisSchema:
    """Generate deterministic fallback analysis for local testing/offline use."""
    subcategory = problem.subcategory if problem.subcategory else "General"
    statement = f"Structured Analysis: {problem.title} — {problem.description}"

    return AIAnalysisSchema(
        problem_id=problem.id,
        structured_statement=statement,
        category=problem.category,
        subcategory=subcategory,
        keywords=extract_fallback_keywords(problem.title, problem.description),
        urgency=problem.urgency,
        confidence=0.85,
        affected_population=problem.affected_population,
        evidence_count=len(problem.evidence),
    )


def _gemini_prompt(problem: ProblemReportSchema) -> str:
    return f"""Analyze this citizen problem for the SAMARTH civic platform.

Title: {problem.title}
Description: {problem.description}
Category: {problem.category}
Subcategory: {problem.subcategory}
Urgency reported by citizen: {problem.urgency}
Affected population: {problem.affected_population}
Location: {problem.location.name}, {problem.location.district} ({problem.location.lat}, {problem.location.lng})
Evidence count: {len(problem.evidence)}

Return only a JSON object with these fields:
structuredStatement (concise formal problem statement),
category (one of Infrastructure, Water & Sanitation, Healthcare, Education, Agriculture, Environment, Public Safety, Transport, Waste Management, Other),
subcategory (refined short label),
keywords (array of 3 to 6 strings),
urgency (one of LOW, MEDIUM, HIGH, CRITICAL),
confidence (number from 0.0 to 1.0),
affectedPopulation (non-negative integer).
Do not invent a problemId or evidenceCount; the application supplies those values."""


def _parse_gemini_analysis(problem: ProblemReportSchema, response_text: str) -> AIAnalysisSchema:
    parsed = json.loads(response_text)
    parsed["problemId"] = problem.id
    parsed["evidenceCount"] = len(problem.evidence)
    return AIAnalysisSchema.model_validate(parsed)


def _generate_with_gemini(problem: ProblemReportSchema) -> AIAnalysisSchema:
    client = genai.Client(api_key=settings.GEMINI_API_KEY.strip())
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=_gemini_prompt(problem),
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    response_text = getattr(response, "text", None)
    if not response_text:
        raise ValueError("Gemini returned an empty response")
    return _parse_gemini_analysis(problem, response_text)


async def analyze_problem_with_gemini(problem: ProblemReportSchema) -> AIAnalysisSchema:
    """Analyze a problem with Gemini without blocking FastAPI's event loop."""
    return await asyncio.to_thread(_generate_with_gemini, problem)


async def analyze_problem_with_ai(
    problem: ProblemReportSchema,
    force_fallback: bool = False,
) -> AIAnalysisSchema:
    """Use Gemini when configured, otherwise use deterministic fallback."""
    api_key = settings.GEMINI_API_KEY.strip() if settings.GEMINI_API_KEY else ""

    if force_fallback or not api_key:
        return generate_fallback_analysis(problem)

    try:
        return await analyze_problem_with_gemini(problem)
    except Exception as exc:
        print(
            f"[AI PROVIDER WARN] Gemini analysis failed ({type(exc).__name__}). "
            "Falling back to deterministic analysis."
        )
        return generate_fallback_analysis(problem)