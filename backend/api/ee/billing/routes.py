from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlmodel import Session

from api.ee.auth.dependencies import get_current_user_id
from api.ee.billing.service import (
    create_checkout_session,
    create_portal_session,
    handle_webhook_event,
)

router = APIRouter(prefix="/billing", tags=["ee-billing"])


class CheckoutRequest(BaseModel):
    price_id: str
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    url: str


class PortalRequest(BaseModel):
    return_url: str


class PortalResponse(BaseModel):
    url: str


def _get_db(request: Request) -> Session:
    """Get database session from container."""
    container = request.app.state.container
    return container.session_factory()


@router.post("/create-checkout-session", response_model=CheckoutResponse)
async def create_checkout(
    body: CheckoutRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(_get_db)],
):
    url = create_checkout_session(
        user_id=user_id,
        price_id=body.price_id,
        success_url=body.success_url,
        cancel_url=body.cancel_url,
        db=db,
    )
    if not url:
        raise HTTPException(status_code=500, detail="Failed to create checkout session")
    return CheckoutResponse(url=url)


@router.post("/create-portal-session", response_model=PortalResponse)
async def create_portal(
    body: PortalRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(_get_db)],
):
    try:
        url = create_portal_session(
            user_id=user_id,
            return_url=body.return_url,
            db=db,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return PortalResponse(url=url)


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Annotated[Session, Depends(_get_db)],
):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")
    try:
        handle_webhook_event(payload, sig_header, db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"status": "ok"}
