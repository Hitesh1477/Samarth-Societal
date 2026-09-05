"""
Base Pydantic configuration shared by all schemas.

The frontend uses camelCase field names (e.g. affectedPopulation, createdAt).
We configure alias_generator=to_camel and populate_by_name=True so that:
  - Pydantic accepts snake_case when constructing models internally.
  - FastAPI serialises all responses as camelCase automatically.
"""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Base model: snake_case internally, camelCase on the wire."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,   # allow both snake_case and camelCase in input
        use_enum_values=True,    # serialise enums as their .value
        from_attributes=True,    # support ORM-style attribute access
    )
