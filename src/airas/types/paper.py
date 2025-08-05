from pydantic import BaseModel
from typing_extensions import TypedDict


class CandidatePaperInfo(TypedDict):
    arxiv_id: str
    arxiv_url: str
    title: str
    authors: list[str]
    published_date: str
    journal: str
    doi: str
    summary: str
    github_url: str
    main_contributions: str
    methodology: str
    experimental_setup: str
    limitations: str
    future_research_directions: str


class PaperContent(BaseModel):
    title: str
    abstract: str
    introduction: str
    related_work: str
    background: str
    method: str
    experimental_setup: str
    results: str
    conclusion: str
