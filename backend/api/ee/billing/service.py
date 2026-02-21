from datetime import datetime, timezone
from uuid import UUID

import stripe
from sqlmodel import Session, select

from api.ee.billing.models import PlanType, SubscriptionModel, SubscriptionStatus
from api.ee.settings import get_ee_settings


def _init_stripe() -> None:
    settings = get_ee_settings()
    stripe.api_key = settings.stripe_api_key


def create_checkout_session(
    user_id: UUID,
    price_id: str,
    success_url: str,
    cancel_url: str,
    db: Session,
) -> str:
    """Create a Stripe Checkout session and return the URL."""
    _init_stripe()

    sub = db.exec(
        select(SubscriptionModel).where(SubscriptionModel.user_id == user_id)
    ).first()

    if sub and sub.stripe_customer_id:
        customer_id = sub.stripe_customer_id
    else:
        customer = stripe.Customer.create(metadata={"user_id": str(user_id)})
        customer_id = customer.id
        if not sub:
            sub = SubscriptionModel(
                user_id=user_id,
                stripe_customer_id=customer_id,
                plan=PlanType.FREE,
                status=SubscriptionStatus.INCOMPLETE,
            )
            db.add(sub)
            db.commit()

    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session.url


def create_portal_session(user_id: UUID, return_url: str, db: Session) -> str:
    """Create a Stripe Billing Portal session and return the URL."""
    _init_stripe()
    sub = db.exec(
        select(SubscriptionModel).where(SubscriptionModel.user_id == user_id)
    ).first()
    if not sub or not sub.stripe_customer_id:
        raise ValueError("No subscription found for user")

    session = stripe.billing_portal.Session.create(
        customer=sub.stripe_customer_id,
        return_url=return_url,
    )
    return session.url


def handle_webhook_event(payload: bytes, sig_header: str, db: Session) -> None:
    """Process a Stripe webhook event."""
    settings = get_ee_settings()
    _init_stripe()

    event = stripe.Webhook.construct_event(
        payload, sig_header, settings.stripe_webhook_secret
    )

    if event["type"] == "checkout.session.completed":
        _handle_checkout_completed(event["data"]["object"], db)
    elif event["type"] in (
        "customer.subscription.updated",
        "customer.subscription.deleted",
    ):
        _handle_subscription_change(event["data"]["object"], db)


def _handle_checkout_completed(session: dict, db: Session) -> None:
    customer_id = session["customer"]
    subscription_id = session["subscription"]

    sub = db.exec(
        select(SubscriptionModel).where(
            SubscriptionModel.stripe_customer_id == customer_id
        )
    ).first()
    if sub:
        sub.stripe_subscription_id = subscription_id
        sub.status = SubscriptionStatus.ACTIVE
        sub.plan = PlanType.PRO
        sub.updated_at = datetime.now(timezone.utc)
        db.add(sub)
        db.commit()


def _handle_subscription_change(subscription: dict, db: Session) -> None:
    subscription_id = subscription["id"]
    status_str = subscription["status"]

    sub = db.exec(
        select(SubscriptionModel).where(
            SubscriptionModel.stripe_subscription_id == subscription_id
        )
    ).first()
    if not sub:
        return

    status_map = {
        "active": SubscriptionStatus.ACTIVE,
        "canceled": SubscriptionStatus.CANCELED,
        "past_due": SubscriptionStatus.PAST_DUE,
        "incomplete": SubscriptionStatus.INCOMPLETE,
        "trialing": SubscriptionStatus.TRIALING,
    }
    sub.status = status_map.get(status_str, SubscriptionStatus.INCOMPLETE)

    period_start = subscription.get("current_period_start")
    period_end = subscription.get("current_period_end")
    if period_start:
        sub.current_period_start = datetime.fromtimestamp(period_start, tz=timezone.utc)
    if period_end:
        sub.current_period_end = datetime.fromtimestamp(period_end, tz=timezone.utc)

    if status_str == "canceled":
        sub.plan = PlanType.FREE

    sub.updated_at = datetime.now(timezone.utc)
    db.add(sub)
    db.commit()
