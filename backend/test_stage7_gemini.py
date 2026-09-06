"""Focused Stage 7 Gemini provider tests; no live Gemini call is required."""

import asyncio
from unittest.mock import patch

from app.main import app
from app.schemas.problems import LocationSchema, ProblemReportSchema
from app.services import ai_provider


def make_problem() -> ProblemReportSchema:
    return ProblemReportSchema(
        id="stage7-problem",
        title="Monsoon waterlogging near the market",
        description="Rainwater blocks the road and affects access to the clinic.",
        category="Infrastructure",
        subcategory="Drainage",
        urgency="HIGH",
        affected_population=1200,
        location=LocationSchema(
            lat=23.3441,
            lng=85.3096,
            name="Main Road",
            district="Ranchi",
        ),
        evidence=[],
        status="SUBMITTED",
        created_at="2026-09-06T00:00:00Z",
        reporter_name="Stage 7 Test",
    )


def test_provider_imports_and_missing_key_uses_fallback() -> None:
    problem = make_problem()
    with patch.object(ai_provider.settings, "GEMINI_API_KEY", ""):
        result = asyncio.run(ai_provider.analyze_problem_with_ai(problem))

    assert result.problem_id == problem.id
    assert result.category == problem.category
    assert 0.0 <= result.confidence <= 1.0
    assert result.evidence_count == 0


def test_gemini_json_is_validated_against_existing_schema() -> None:
    problem = make_problem()
    result = ai_provider._parse_gemini_analysis(
        problem,
        '{"structuredStatement":"Road access is blocked.",'
        '"category":"Infrastructure","subcategory":"Drainage",'
        '"keywords":["waterlogging","road"],"urgency":"HIGH",'
        '"confidence":0.91,"affectedPopulation":1200}',
    )

    assert result.problem_id == problem.id
    assert result.evidence_count == 0
    assert result.affected_population == 1200


def test_gemini_failure_uses_fallback() -> None:
    problem = make_problem()
    with (
        patch.object(ai_provider.settings, "GEMINI_API_KEY", "configured-but-not-printed"),
        patch.object(
            ai_provider,
            "analyze_problem_with_gemini",
            side_effect=RuntimeError("simulated provider failure"),
        ),
    ):
        result = asyncio.run(ai_provider.analyze_problem_with_ai(problem))

    assert result.problem_id == problem.id
    assert result.structured_statement.startswith("Structured Analysis:")


def test_analyze_endpoint_contract_remains_registered() -> None:
    routes = {(route.path, method) for route in app.routes for method in route.methods or set()}
    assert ("/api/problems/{problem_id}/analyze", "POST") in routes


if __name__ == "__main__":
    test_provider_imports_and_missing_key_uses_fallback()
    test_gemini_json_is_validated_against_existing_schema()
    test_gemini_failure_uses_fallback()
    test_analyze_endpoint_contract_remains_registered()
    print("Stage 7 Gemini provider tests passed")