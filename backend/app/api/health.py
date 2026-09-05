"""
Health check endpoint.

GET /health → { "status": "ok", "service": "samarth-backend" }
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health() -> HealthResponse:
    """Simple liveness probe — no external dependencies queried."""
    return HealthResponse(status="ok", service="samarth-backend")
