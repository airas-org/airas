from uuid import UUID

from pydantic import BaseModel, Field


class SessionCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class SessionResponse(BaseModel):
    id: UUID
    title: str
