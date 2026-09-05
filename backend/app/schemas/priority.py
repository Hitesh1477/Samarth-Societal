"""
Priority domain schemas.

Matches frontend interfaces in frontend/src/types/index.ts:
- PriorityBreakdown
- PriorityScore
- PriorityLevel ('HIGH' | 'MEDIUM' | 'LOW')
"""

from pydantic import Field
from app.schemas.base import CamelModel
from app.schemas.enums import PriorityLevel


class ScoreFactorSchema(CamelModel):
    """Sub-score item containing score and max score."""
    score: float = Field(ge=0.0)
    max: float = Field(ge=0.0)


class PriorityBreakdownSchema(CamelModel):
    """
    Matches frontend `PriorityBreakdown` interface exactly.

    camelCase aliases (via CamelModel):
        safetyRisk, populationImpact, recurrence, evidence, locationRisk
    """
    safety_risk: ScoreFactorSchema
    population_impact: ScoreFactorSchema
    recurrence: ScoreFactorSchema
    evidence: ScoreFactorSchema
    location_risk: ScoreFactorSchema


class PriorityScoreSchema(CamelModel):
    """
    Matches frontend `PriorityScore` interface exactly.

    camelCase aliases (via CamelModel):
        challengeId, total, level, breakdown, explanation
    """
    challenge_id: str
    total: float = Field(ge=0.0, le=100.0)
    level: PriorityLevel
    breakdown: PriorityBreakdownSchema
    explanation: str
