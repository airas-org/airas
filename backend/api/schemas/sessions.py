from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


class SessionCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    created_by: UUID


class SessionResponse(BaseModel):
    id: UUID
    title: str
    created_at: datetime


def get_current_user_id() -> UUID:
    # NOTE: 認証導入まで固定値にする。後でJWT等に置き換えを行う。
    return SYSTEM_USER_ID
