"""
Map and Geospatial domain schemas — Stage 6B.

Matches the frontend MapData contract in frontend/src/types/index.ts:

export interface MapData {
  challenges: MapChallenge[];
  hotspots: { name: string; count: number }[];
}

CamelModel handles camelCase field conversion automatically.
"""

from typing import Optional
from app.schemas.base import CamelModel
from app.schemas.common import MapChallengeSchema


class HotspotSchema(CamelModel):
    """Hotspot item matching frontend { name: string, count: number }."""
    name: str
    count: int


class MapDataSchema(CamelModel):
    """
    MapData response schema matching frontend interface.
    """
    challenges: list[MapChallengeSchema]
    hotspots: list[HotspotSchema]
