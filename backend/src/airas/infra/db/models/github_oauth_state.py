from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlmodel import Field, SQLModel


class GitHubOAuthStateModel(SQLModel, table=True):
    __tablename__ = "github_oauth_states"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(nullable=False, index=True)
    state: str = Field(
        sa_column=Column(String, nullable=False, unique=True, index=True)
    )

    created_at: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
        default_factory=lambda: datetime.now().astimezone(),
    )
