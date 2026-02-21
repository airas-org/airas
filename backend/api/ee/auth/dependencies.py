from uuid import UUID

from fastapi import Request

from api.ee.auth.middleware import extract_user_id_from_request
from api.ee.settings import get_ee_settings

SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def get_current_user_id(request: Request) -> UUID:
    """Return user ID from JWT if EE is enabled, otherwise return SYSTEM_USER_ID."""
    settings = get_ee_settings()
    if not settings.enabled:
        return SYSTEM_USER_ID
    return extract_user_id_from_request(request)
