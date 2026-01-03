from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlmodel import Field, SQLModel


class AssistedResearchSessionModel(SQLModel, table=True):
    __tablename__ = "assisted_research_sessions"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    title: str = Field(index=True)

    created_at: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
        default_factory=lambda: datetime.now().astimezone(),
    )
    created_by: UUID = Field(nullable=False, index=True)
    active_head_step_id: UUID | None = Field(default=None, index=True)
