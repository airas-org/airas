from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class FeedbackCategory(str, Enum):
    BUG = "bug"
    FEATURE = "feature"
    GENERAL = "general"
    OTHER = "other"


class FeedbackModel(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    category: FeedbackCategory
    subject: str
    detail: str
    email: str | None = None
    created_by: UUID
    created_at: datetime = Field(
        default_factory=lambda: datetime.now().astimezone(),
    )
