"""
AI domain schemas.

Matches frontend AIAnalysis interface in frontend/src/types/index.ts.
CamelModel converts snake_case field names to camelCase for the API wire.
"""

from pydantic import Field
from app.schemas.base import CamelModel
from app.schemas.enums import ProblemCategory, UrgencyLevel


class AIAnalysisSchema(CamelModel):
    """
    Matches frontend `AIAnalysis` interface exactly.

    camelCase aliases (via CamelModel):
        problemId, structuredStatement, category, subcategory,
        keywords, urgency, confidence, affectedPopulation, evidenceCount
    """
    problem_id: str
    structured_statement: str
    category: ProblemCategory
    subcategory: str
    keywords: list[str] = Field(default_factory=list)
    urgency: UrgencyLevel
    confidence: float = Field(ge=0.0, le=1.0)
    affected_population: int = Field(ge=0)
    evidence_count: int = Field(ge=0)
