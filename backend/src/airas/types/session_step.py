from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Column
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlmodel import Field, SQLModel


class SessionStepType(str, Enum):
    RETRIEVE = "retrieve"
    HYPOTHESIS = "hypothesis"
    DESIGN = "design"
    CODE = "code"
    EXPERIMENT = "experiment"
    ANALYSIS = "analysis"
    WRITE = "write"
    PUBLISH = "publish"
    OTHER = "other"


class SessionStepModel(SQLModel, table=True):
    __tablename__ = "session_steps"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    session_id: UUID = Field(nullable=False, index=True)
    step_type: SessionStepType = Field(
        sa_column=Column(
            SqlEnum(SessionStepType, name="session_step_type"), nullable=False
        )
    )
    content: Any = Field(sa_column=Column(JSONB, nullable=False))
    schema_version: int = Field(nullable=False)
    created_by: UUID = Field(nullable=False, index=True)
    created_at: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
        default_factory=lambda: datetime.now().astimezone(),
    )
    is_complated: bool = Field(default=False, nullable=False)
