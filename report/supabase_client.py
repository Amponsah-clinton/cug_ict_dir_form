from supabase import create_client, Client
from django.conf import settings

_anon_client: Client | None = None
_service_client: Client | None = None


def get_client() -> Client:
    global _anon_client
    if _anon_client is None:
        _anon_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _anon_client


def get_service_client() -> Client:
    global _service_client
    if _service_client is None:
        _service_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    return _service_client
