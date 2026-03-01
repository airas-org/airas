from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from airas.container import Container
from airas.usecases.ee.plan_service import PlanService
from api.ee.auth.dependencies import get_current_user_id
from api.schemas.ee import UserPlanResponse

router = APIRouter(prefix="/plan", tags=["ee-plan"])


@router.get("", response_model=UserPlanResponse)
@inject
def get_plan(
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[PlanService, Depends(Provide[Container.plan_service])],
) -> UserPlanResponse:
    plan = service.get_plan(current_user_id)
    return UserPlanResponse(
        plan_type=plan.plan_type,
        status=plan.status,
        stripe_customer_id=plan.stripe_customer_id,
    )
