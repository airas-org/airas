import enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Column, Enum, Field, SQLModel


class PlanType(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    INCOMPLETE = "incomplete"
    TRIALING = "trialing"


class SubscriptionModel(SQLModel, table=True):
    __tablename__ = "subscriptions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(index=True, nullable=False)
    stripe_customer_id: str = Field(index=True, nullable=False)
    stripe_subscription_id: str | None = Field(default=None, index=True)
    plan: PlanType = Field(
        sa_column=Column(Enum(PlanType), nullable=False, default=PlanType.FREE)
    )
    status: SubscriptionStatus = Field(
        sa_column=Column(
            Enum(SubscriptionStatus),
            nullable=False,
            default=SubscriptionStatus.INCOMPLETE,
        )
    )
    current_period_start: datetime | None = Field(default=None)
    current_period_end: datetime | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
