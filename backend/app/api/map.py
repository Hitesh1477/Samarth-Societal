"""
Map & Geospatial API router — Stage 6B.

Routes:
    GET /api/map/challenges → get challenge map markers & district hotspots
"""

from typing import Optional
from fastapi import APIRouter, Query, status

from app.schemas.map import MapDataSchema
from app.services import map as map_service

router = APIRouter(prefix="/api/map", tags=["map"])


@router.get(
    "/challenges",
    response_model=MapDataSchema,
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="Get challenge map markers and district hotspots",
    responses={
        200: {"description": "Map data retrieved successfully"},
        500: {"description": "Database error"},
    },
)
async def get_map_challenges(
    category: Optional[str] = Query(None, description="Filter by category"),
    priority: Optional[str] = Query(None, description="Filter by priority level (HIGH|MEDIUM|LOW)"),
    district: Optional[str] = Query(None, description="Filter by district"),
) -> MapDataSchema:
    """
    Return challenge map markers and district hotspots matching frontend MapData contract:
    - Only returns challenges with valid latitude (-90 to 90) and longitude (-180 to 180).
    - Hotspots are aggregated by district and sorted count descending.
    - Supports optional query filters: `category`, `priority`, `district`.
    """
    return await map_service.get_map_challenges(
        category=category,
        priority=priority,
        district=district,
    )
