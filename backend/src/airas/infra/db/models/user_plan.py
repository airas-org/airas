import enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, Index, String
from sqlmodel import Field, SQLModel


class PlanType(str, enum.Enum):
    FREE = "free"
    PRO = "pro"


class PlanStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"


class UserPlanModel(SQLModel, table=True):
    __tablename__ = "user_plans"
    __table_args__ = (Index("ix_user_plans_user_id", "user_id", unique=True),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(nullable=False, unique=True)
    plan_type: PlanType = Field(
        default=PlanType.FREE,
        sa_column=Column(String, nullable=False, server_default="free"),
    )
    stripe_customer_id: str | None = Field(default=None)
    stripe_subscription_id: str | None = Field(default=None)
    status: PlanStatus = Field(
        default=PlanStatus.ACTIVE,
        sa_column=Column(String, nullable=False, server_default="active"),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
