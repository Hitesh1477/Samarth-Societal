"""Safe Supabase configuration and admin-write diagnostic.

Run from backend/: python diagnose_supabase.py
This prints only booleans, client type, operation status, and error types.
"""

import uuid

from app.core.config import settings
from app.core.database import get_supabase_admin_client


def main() -> None:
    print("SUPABASE_URL exists:", bool(settings.SUPABASE_URL))
    print("SUPABASE_SERVICE_ROLE_KEY exists:", bool(settings.SUPABASE_SERVICE_ROLE_KEY))
    print("Supabase client type: admin/service-role client")

    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        print("Admin database operation succeeded: False")
        print("Admin database operation error type: MissingConfiguration")
        return

    try:
        client = get_supabase_admin_client()
        probe_id = str(uuid.uuid4())
        client.table("organizations").insert({
            "id": probe_id,
            "name": "SAMARTH admin client diagnostic",
            "type": "OTHER",
        }).execute()
        client.table("organizations").update({
            "name": "SAMARTH admin client diagnostic updated",
        }).eq("id", probe_id).execute()
        client.table("organizations").delete().eq("id", probe_id).execute()
        print("Admin database operation succeeded: True")
    except Exception as exc:
        try:
            if "probe_id" in locals():
                get_supabase_admin_client().table("organizations").delete().eq("id", probe_id).execute()
        except Exception:
            pass
        print("Admin database operation succeeded: False")
        print("Admin database operation error type:", type(exc).__name__)


if __name__ == "__main__":
    main()