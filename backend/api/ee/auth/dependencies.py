from uuid import UUID

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from airas.repository.user_api_key_repository import UserApiKeyRepository
from airas.repository.user_plan_repository import UserPlanRepository
from airas.usecases.ee.api_key_resolver import ApiKeyResolver
from api.ee.auth.middleware import extract_user_id_from_request
from api.ee.dependencies import EEDBSession
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


def require_api_keys(
    request: Request,
    db: EEDBSession,
    _credentials: HTTPAuthorizationCredentials | None = _bearer_dependency,
) -> None:
    """Raise 403 if the user has no API keys configured."""
    settings = get_ee_settings()
    if not settings.enabled:
        return
    user_id = extract_user_id_from_request(request)
    plan_repo = UserPlanRepository(db=db)
    api_key_repo = UserApiKeyRepository(db=db)
    resolver = ApiKeyResolver(plan_repo=plan_repo, api_key_repo=api_key_repo)
    keys = resolver.resolve_keys(user_id)
    if not keys:
        raise HTTPException(
            status_code=403,
            detail="API keys are not configured. Please set your API keys in the Integration page.",
        )
