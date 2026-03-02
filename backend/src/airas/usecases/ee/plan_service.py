import os
from uuid import UUID

import stripe

from airas.infra.db.models.user_plan import PlanStatus, PlanType, UserPlanModel
from airas.repository.user_plan_repository import UserPlanRepository


class PlanService:
    def __init__(self, repo: UserPlanRepository):
        self.repo = repo
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

    def get_plan(self, user_id: UUID) -> UserPlanModel:
        plan = self.repo.get_by_user(user_id)
        if plan is None:
            plan = UserPlanModel(
                user_id=user_id,
                plan_type=PlanType.FREE,
                status=PlanStatus.ACTIVE,
            )
            return self.repo.create(plan)
        return plan

    def create_checkout_session(
        self, *, user_id: UUID, success_url: str, cancel_url: str
    ) -> str:
        plan = self.get_plan(user_id)
        price_id = os.getenv("STRIPE_PRICE_ID", "")

        customer_id = plan.stripe_customer_id
        if not customer_id:
            customer = stripe.Customer.create(metadata={"user_id": str(user_id)})
            customer_id = customer.id
            plan.stripe_customer_id = customer_id
            self.repo.db.add(plan)
            self.repo.db.commit()

        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return session.url or ""

    def handle_webhook_event(self, event: dict) -> None:
        event_type = event.get("type", "")
        data_obj = event.get("data", {}).get("object", {})

        if event_type == "checkout.session.completed":
            customer_id = data_obj.get("customer", "")
            subscription_id = data_obj.get("subscription", "")
            self._activate_pro(customer_id, subscription_id)
        elif event_type == "customer.subscription.deleted":
            customer_id = data_obj.get("customer", "")
            self._deactivate_pro(customer_id)

    def _activate_pro(self, customer_id: str, subscription_id: str) -> None:
        from sqlmodel import select

        stmt = select(UserPlanModel).where(
            UserPlanModel.stripe_customer_id == customer_id
        )
        plan = self.repo.db.exec(stmt).first()
        if plan:
            plan.plan_type = PlanType.PRO
            plan.stripe_subscription_id = subscription_id
            plan.status = PlanStatus.ACTIVE
            self.repo.db.add(plan)
            self.repo.db.commit()

    def _deactivate_pro(self, customer_id: str) -> None:
        from sqlmodel import select

        stmt = select(UserPlanModel).where(
            UserPlanModel.stripe_customer_id == customer_id
        )
        plan = self.repo.db.exec(stmt).first()
        if plan:
            plan.plan_type = PlanType.FREE
            plan.status = PlanStatus.CANCELED
            self.repo.db.add(plan)
            self.repo.db.commit()

    def cancel_subscription(self, user_id: UUID) -> None:
        plan = self.get_plan(user_id)
        if plan.plan_type != PlanType.PRO or not plan.stripe_subscription_id:
            return
        stripe.Subscription.cancel(plan.stripe_subscription_id)
        plan.plan_type = PlanType.FREE
        plan.status = PlanStatus.CANCELED
        plan.stripe_subscription_id = None
        self.repo.db.add(plan)
        self.repo.db.commit()

    def close(self) -> None:
        self.repo.db.close()
