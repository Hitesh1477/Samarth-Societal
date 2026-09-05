"""
Solver matching schemas — representations for solver profiles and match responses.

All models inherit from CamelModel so that snake_case Python attributes
automatically map to camelCase JSON attributes expected by the frontend TypeScript contract.
"""

from typing import Optional
from app.schemas.base import CamelModel
from app.schemas.enums import SolverType
from app.schemas.common import SolverMatchSchema


class SolverProfileSchema(CamelModel):
    """Internal model for solver profile database rows / objects."""
    id: str
    name: str
    type: SolverType
    department: Optional[str] = None
    district: str = ""
    state: str = ""
    categories: list[str] = []
    expertise: list[str] = []
    capacity: str = "HIGH"
    equipment: list[str] = []
    previous_projects: list[str] = []
    description: str = ""


__all__ = ["SolverProfileSchema", "SolverMatchSchema"]
