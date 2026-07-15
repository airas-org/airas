from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class VerificationModel(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str = "名称未設定"
    query: str = ""
    created_by: UUID
    created_at: datetime = Field(
        default_factory=lambda: datetime.now().astimezone(),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now().astimezone(),
    )
    phase: str = "initial"
    proposed_methods: list[dict] | None = None
    selected_method_id: str | None = None
    verification_method: dict | None = None
    plan: dict | None = None
    repository_name: str | None = None
    github_owner: str | None = None
    github_url: str | None = None
    workflow_run_id: int | None = None
    modification_notes: str | None = None
    code_generation_status: str | None = None
    code_generation_conclusion: str | None = None
    implementation: dict | None = None
    paper_draft: dict | None = None
