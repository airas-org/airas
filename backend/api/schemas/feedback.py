import re

from pydantic import BaseModel, Field, field_validator

from airas.infra.db.models.feedback import FeedbackCategory


class CreateFeedbackRequestBody(BaseModel):
    category: FeedbackCategory
    subject: str = Field(min_length=1, max_length=255)
    detail: str = Field(min_length=1, max_length=5000)
    email: str | None = Field(default=None, max_length=255)

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError("Invalid email format")
        return v


class CreateFeedbackResponseBody(BaseModel):
    id: str
    category: str
    subject: str
    detail: str
    email: str | None
    created_at: str
