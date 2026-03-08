from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlmodel import Field, SQLModel


class VerificationModel(SQLModel, table=True):
    __tablename__ = "verifications"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    title: str = Field(default="名称未設定", index=True)
    query: str = Field(
        default="", sa_column=Column(String, nullable=False, server_default="")
    )
    created_by: UUID = Field(nullable=False, index=True)
    created_at: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
        default_factory=lambda: datetime.now().astimezone(),
    )
    updated_at: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
        default_factory=lambda: datetime.now().astimezone(),
    )
    phase: str = Field(
        default="initial",
        sa_column=Column(String, nullable=False, server_default="initial"),
    )
    proposed_methods: list[dict] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    selected_method_id: str | None = Field(
        default=None, sa_column=Column(String, nullable=True)
    )
    verification_method: dict | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    plan: dict | None = Field(default=None, sa_column=Column(JSONB, nullable=True))
    repository_name: str | None = Field(
        default=None, sa_column=Column(String, nullable=True)
    )
    github_owner: str | None = Field(
        default=None, sa_column=Column(String, nullable=True)
    )
    github_url: str | None = Field(
        default=None, sa_column=Column(String, nullable=True)
    )
    workflow_run_id: int | None = Field(default=None, nullable=True)
    modification_notes: str | None = Field(
        default=None, sa_column=Column(String, nullable=True)
    )
    code_generation_status: str | None = Field(
        default=None, sa_column=Column(String, nullable=True)
    )
    code_generation_conclusion: str | None = Field(
        default=None, sa_column=Column(String, nullable=True)
    )
    implementation: dict | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    paper_draft: dict | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
