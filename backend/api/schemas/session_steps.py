from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from airas.types.session_step import SessionStepType


class SessionStepCreateRequest(BaseModel):
    session_id: UUID
    step_type: SessionStepType
    content: Any
    schema_version: int = Field(ge=1)
    created_by: UUID
    is_complated: bool = False


class SessionStepResponse(BaseModel):
    id: UUID
    session_id: UUID
    step_type: SessionStepType
    content: Any
    schema_version: int
    created_by: UUID
    created_at: datetime
    is_complated: bool
