from pydantic import BaseModel, Field

# TODO:確認する
class ArxivInfo(BaseModel):
    id: str = Field(..., description="")
    url: str = Field(..., description="")
    title: str = Field(..., description="")
    authors: list[str] = Field(..., description="")
    published_date: str = Field(..., description="")
    summary: str = Field(..., description="")
