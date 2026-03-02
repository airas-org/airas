from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from airas.container import Container
from airas.usecases.ee.api_key_resolver import ApiKeyResolver
from api.ee.auth.middleware import extract_user_id_from_request
from api.ee.settings import get_ee_settings

SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

# Show "Authorize" button in Swagger UI when EE is enabled
_bearer_scheme = HTTPBearer(auto_error=False)
_bearer_dependency = Depends(_bearer_scheme)


def get_current_user_id(
    request: Request,
    _credentials: HTTPAuthorizationCredentials | None = _bearer_dependency,
) -> UUID:
    """Return user ID from JWT if EE is enabled, otherwise return SYSTEM_USER_ID."""
    settings = get_ee_settings()
    if not settings.enabled:
        return SYSTEM_USER_ID
    return extract_user_id_from_request(request)


@inject
def require_api_keys(
    request: Request,
    _credentials: HTTPAuthorizationCredentials | None = _bearer_dependency,
    resolver: Annotated[
        ApiKeyResolver, Depends(Provide[Container.api_key_resolver])
    ] = None,
) -> None:
    """Raise 403 if the user has no API keys configured."""
    settings = get_ee_settings()
    if not settings.enabled:
        return
    user_id = extract_user_id_from_request(request)
    keys = resolver.resolve_keys(user_id)
    if not keys:
        raise HTTPException(
            status_code=403,
            detail="API keys are not configured. Please set your API keys in the Integration page.",
        )
