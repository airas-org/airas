from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from airas.repository.user_api_key_repository import UserApiKeyRepository
from airas.repository.user_plan_repository import UserPlanRepository
from airas.usecases.ee.api_key_resolver import ApiKeyResolver
from airas.usecases.ee.plan_service import PlanService
from api.ee.auth.dependencies import get_current_user_id
from api.ee.dependencies import EEDBSession
from api.schemas.ee import UserPlanResponse

# Mapping from env var name to provider display name
_ENV_TO_PROVIDER: dict[str, str] = {
    "OPENAI_API_KEY": "openai",
    "ANTHROPIC_API_KEY": "anthropic",
    "GEMINI_API_KEY": "google",
}

router = APIRouter(prefix="/plan", tags=["ee-plan"])


@router.get("", response_model=UserPlanResponse)
def get_plan(
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: EEDBSession,
) -> UserPlanResponse:
    plan_repo = UserPlanRepository(db=db)
    api_key_repo = UserApiKeyRepository(db=db)
    service = PlanService(repo=plan_repo)
    resolver = ApiKeyResolver(plan_repo=plan_repo, api_key_repo=api_key_repo)

    plan = service.get_plan(current_user_id)
    is_pro = plan.plan_type == "pro"
    keys = resolver.resolve_keys(current_user_id)
    available_providers = [
        _ENV_TO_PROVIDER[env_name] for env_name in keys if env_name in _ENV_TO_PROVIDER
    ]
    return UserPlanResponse(
        plan_type=plan.plan_type,
        status=plan.status,
        stripe_customer_id=plan.stripe_customer_id,
        requires_api_keys=not is_pro,
        available_providers=available_providers,
    )
