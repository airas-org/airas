from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlmodel import Field, SQLModel


class StepRunLinkModel(SQLModel, table=True):
    __tablename__ = "step_run_links"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    from_step_run_id: UUID = Field(nullable=False, index=True)
    to_step_run_id: UUID = Field(nullable=False, index=True)
    created_at: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
        default_factory=lambda: datetime.now().astimezone(),
    )
