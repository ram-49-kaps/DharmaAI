import os
from supabase import create_client, Client

_client: Client = None


def get_supabase() -> Client:
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
        _client = create_client(url, key)
    return _client


def init_db():
    try:
        get_supabase().table("user_profiles").select("uid").limit(1).execute()
        print("[DB] Supabase connected.")
    except Exception as e:
        print(f"[DB] Supabase connection error: {e}")
        raise
