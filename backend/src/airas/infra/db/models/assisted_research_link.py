from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, UniqueConstraint
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlmodel import Field, SQLModel


class AssistedResearchLinkModel(SQLModel, table=True):
    __tablename__ = "assisted_research_links"
    __table_args__ = (
        UniqueConstraint("from_step_id", "to_step_id", name="uq_assisted_link"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    from_step_id: UUID = Field(nullable=False, index=True)
    to_step_id: UUID = Field(nullable=False, index=True)
    created_at: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
        default_factory=lambda: datetime.now().astimezone(),
    )
