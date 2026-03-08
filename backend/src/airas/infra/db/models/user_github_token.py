from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, Index, String, UniqueConstraint
from sqlmodel import Field, SQLModel


class UserGitHubTokenModel(SQLModel, table=True):
    __tablename__ = "user_github_tokens"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_github_token_user_id"),
        Index("ix_user_github_tokens_user_id", "user_id"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(nullable=False)
    encrypted_token: str = Field(nullable=False)
    github_login: str = Field(sa_column=Column(String, nullable=False))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"server_default": "now()"},
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"server_default": "now()"},
    )
