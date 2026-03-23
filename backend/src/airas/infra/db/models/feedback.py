from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
from sqlmodel import Field, SQLModel


class FeedbackCategory(str, Enum):
    BUG = "bug"
    FEATURE = "feature"
    GENERAL = "general"
    OTHER = "other"


class FeedbackModel(SQLModel, table=True):
    __tablename__ = "feedbacks"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True),
    )
    category: FeedbackCategory = Field(sa_column=Column(String(50), nullable=False))
    subject: str = Field(sa_column=Column(String(255), nullable=False))
    detail: str = Field(sa_column=Column(Text, nullable=False))
    email: str | None = Field(
        default=None, sa_column=Column(String(255), nullable=True)
    )
    created_by: UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    )
    created_at: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
        )
    )
