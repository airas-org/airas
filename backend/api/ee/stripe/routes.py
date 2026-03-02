import os
from typing import Annotated
from uuid import UUID

import stripe
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Request

from airas.container import Container
from airas.usecases.ee.plan_service import PlanService
from api.ee.auth.dependencies import get_current_user_id
from api.schemas.ee import CheckoutRequest, CheckoutResponse

router = APIRouter(prefix="/stripe", tags=["ee-stripe"])


@router.post("/checkout", response_model=CheckoutResponse)
@inject
def create_checkout(
    request: CheckoutRequest,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[PlanService, Depends(Provide[Container.plan_service])],
) -> CheckoutResponse:
    url = service.create_checkout_session(
        user_id=current_user_id,
        success_url=request.success_url,
        cancel_url=request.cancel_url,
    )
    return CheckoutResponse(checkout_url=url)


@router.post("/cancel")
@inject
def cancel_subscription(
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[PlanService, Depends(Provide[Container.plan_service])],
):
    service.cancel_subscription(current_user_id)
    return {"status": "canceled"}


@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except (ValueError, stripe.SignatureVerificationError) as err:
        raise HTTPException(
            status_code=400, detail="Invalid webhook signature"
        ) from err

    from sqlalchemy.orm import sessionmaker
    from sqlmodel import Session, create_engine

    from airas.repository.user_plan_repository import UserPlanRepository

    database_url = os.getenv("DATABASE_URL", "")
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_engine(database_url)
    factory = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
    with factory() as session:
        repo = UserPlanRepository(db=session)
        plan_service = PlanService(repo=repo)
        plan_service.handle_webhook_event(event)

    return {"received": True}
