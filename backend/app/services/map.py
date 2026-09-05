"""
Map & Geospatial service — Stage 6B.

Implements:
  - get_map_challenges() → GET /api/map/challenges

Rules:
  - Queries challenges from Supabase.
  - Filters out records with invalid coordinates (lat not between -90 and 90, lng not between -180 and 180).
  - Supports filtering by category, priority, and district.
  - Generates deterministic hotspots by district sorted count descending.
"""

from collections import Counter
from typing import Any, Optional

from app.core.database import get_supabase_admin_client
from app.schemas.common import MapChallengeSchema
from app.schemas.map import HotspotSchema, MapDataSchema


def _is_valid_coordinate(lat: Any, lng: Any) -> bool:
    """Validate latitude (-90 to 90) and longitude (-180 to 180)."""
    try:
        flat = float(lat)
        flng = float(lng)
        return -90.0 <= flat <= 90.0 and -180.0 <= flng <= 180.0 and not (flat == 0.0 and flng == 0.0)
    except (ValueError, TypeError):
        return False


async def get_map_challenges(
    category: Optional[str] = None,
    priority: Optional[str] = None,
    district: Optional[str] = None,
) -> MapDataSchema:
    """
    Fetch challenges with valid geospatial coordinates and build district hotspots.
    """
    client = get_supabase_admin_client()

    query = client.table("challenges").select("*")

    if category and category.lower() != "all":
        query = query.eq("category", category)
    if district and district.lower() != "all":
        query = query.eq("district", district)

    try:
        res = query.execute()
        rows = res.data or []
    except Exception as exc:
        print(f"[MAP SERVICE] Supabase fetch challenges error: {exc}")
        rows = []

    valid_challenges: list[MapChallengeSchema] = []
    district_counts: Counter = Counter()

    for r in rows:
        lat = r.get("lat")
        lng = r.get("lng")

        # Skip invalid or missing coordinates
        if not _is_valid_coordinate(lat, lng):
            continue

        prio_val = float(r.get("priority", 50.0))
        prio_lvl = str(r.get("priority_level", "MEDIUM")).upper()

        # Apply priority level filter if provided
        if priority and priority.lower() != "all" and prio_lvl != priority.upper():
            continue

        dist_name = str(r.get("district") or r.get("location_name") or "Unknown District").strip()
        if dist_name:
            district_counts[dist_name] += 1

        valid_challenges.append(
            MapChallengeSchema(
                id=str(r["id"]),
                title=str(r.get("title", "")),
                lat=float(lat),
                lng=float(lng),
                priority=prio_val,
                priority_level=prio_lvl,
                report_count=int(r.get("report_count", 1)),
                affected_population=int(r.get("affected_population", 0)),
                status=str(r.get("status", "NEW")),
                category=str(r.get("category", "Other")),
                district=dist_name,
            )
        )

    # Sort hotspots by count descending
    hotspots = [
        HotspotSchema(name=name, count=count)
        for name, count in sorted(district_counts.items(), key=lambda item: item[1], reverse=True)
    ]

    return MapDataSchema(
        challenges=valid_challenges,
        hotspots=hotspots,
    )
