"""
Supabase client initialisation.

Two clients are provided:
- `get_supabase_client()`        → uses ANON key  (row-level-security respected)
- `get_supabase_admin_client()`  → uses SERVICE ROLE key (bypasses RLS)
"""

from functools import lru_cache
from supabase import create_client, Client
from fastapi import HTTPException, status
from app.core.config import settings


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
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
