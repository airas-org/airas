from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, String
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlmodel import Field, SQLModel

from airas.infra.db.models.e2e import Status, StepType


class AssistedResearchStepModel(SQLModel, table=True):
    __tablename__ = "assisted_research_steps"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    session_id: UUID = Field(nullable=False, index=True)

    created_by: UUID = Field(nullable=False, index=True)
    created_at: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
        default_factory=lambda: datetime.now().astimezone(),
    )

    status: Status = Field(
        sa_column=Column(SqlEnum(Status, name="status"), nullable=False),
        default=Status.PENDING,
    )
    step_type: StepType = Field(
        sa_column=Column(SqlEnum(StepType, name="step_type"), nullable=False)
    )
    error_message: Optional[str] = Field(
        default=None, sa_column=Column(String, nullable=True)
    )
    result: Any = Field(sa_column=Column(JSONB, nullable=False))
    schema_version: int = Field(nullable=False)
