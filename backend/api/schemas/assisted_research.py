from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from airas.infra.db.models.e2e import Status, StepType


# session
class AssistedResearchSessionCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class AssistedResearchSessionResponse(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    created_by: UUID
    active_head_step_id: UUID | None


# step
class AssistedResearchStepCreateRequest(BaseModel):
    session_id: UUID
    status: Status
    step_type: StepType
    error_message: str | None
    result: Any
    schema_version: int = Field(ge=1)


class AssistedResearchStepResponse(BaseModel):
    id: UUID
    session_id: UUID
    created_by: UUID
    created_at: datetime
    status: Status
    step_type: StepType
    error_message: str | None
    result: Any
    schema_version: int


# link
class AssistedResearchLinkCreateRequest(BaseModel):
    from_step_id: UUID
    to_step_id: UUID


class AssistedResearchLinkResponse(BaseModel):
    from_step_id: UUID
    to_step_id: UUID


class AssistedResearchLinkListResponse(BaseModel):
    links: list[AssistedResearchLinkResponse]
