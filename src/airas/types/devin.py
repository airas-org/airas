from pydantic import BaseModel, Field

class DevinInfo(BaseModel):
    session_id: str = Field(..., description="")
    # TODO: session_idから作れるなら、なくていいかも、確認する
    devin_url: str = Field(..., description="")
