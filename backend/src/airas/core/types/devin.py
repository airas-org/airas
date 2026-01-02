from pydantic import BaseModel, Field


class DevinInfo(BaseModel):
    session_id: str = Field(..., description="")
    devin_url: str = Field(..., description="")
