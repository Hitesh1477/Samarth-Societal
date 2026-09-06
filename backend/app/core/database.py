"""
Supabase client initialisation.

Two clients are provided:
- `get_supabase_client()`        → uses ANON key  (row-level-security respected)
- `get_supabase_admin_client()`  → uses SERVICE ROLE key (bypasses RLS)
"""

import base64
import json
from functools import lru_cache
from supabase import create_client, Client
from fastapi import HTTPException, status
from app.core.config import settings


def _jwt_role(key: str) -> str | None:
    """Read only the non-secret role claim from a Supabase JWT."""
    try:
        payload = key.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload.encode("ascii"))
        role = json.loads(decoded).get("role")
        return role if isinstance(role, str) else None
    except (IndexError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return None


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Return a singleton Supabase client using the anon key."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY.",
        )
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)


@lru_cache(maxsize=1)
def get_supabase_admin_client() -> Client:
    """Return a singleton Supabase admin client using the service role key."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.",
        )

    role = _jwt_role(settings.SUPABASE_SERVICE_ROLE_KEY)
    if (
        settings.SUPABASE_SERVICE_ROLE_KEY == settings.SUPABASE_ANON_KEY
        or role != "service_role"
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database admin client is not configured with a service-role key.",
        )

    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
