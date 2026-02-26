from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlmodel import Field, SQLModel


class GitHubSettingsModel(SQLModel, table=True):
    __tablename__ = "github_settings"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(nullable=False, unique=True, index=True)
    github_token: str = Field(sa_column=Column(String, nullable=False))
    github_username: str | None = Field(
        default=None, sa_column=Column(String, nullable=True)
    )

    created_at: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
        default_factory=lambda: datetime.now().astimezone(),
    )
    updated_at: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
        default_factory=lambda: datetime.now().astimezone(),
    )
