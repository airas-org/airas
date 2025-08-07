from pydantic import BaseModel, Field


# TODO:確認する
class OpenAlexInfo(BaseModel):
    id: str = Field(..., description="")
    doi: str = Field(..., description="")
    display_name: str = Field(..., description="")
    publication_year: str = Field(..., description="")
    publication_date: str = Field(..., description="")
    authorships: str = Field(..., description="")
    biblio: str = Field(..., description="")
    primary_location: str = Field(..., description="")
