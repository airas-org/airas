from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlmodel import Field, SQLModel


class SessionModel(SQLModel, table=True):
    __tablename__ = "sessions"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    title: str = Field(index=True)

    created_at: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
        default_factory=lambda: datetime.now().astimezone(),
    )
