from typing import TypedDict


class CandidatePaperInfo(TypedDict):
    arxiv_id: str
    arxiv_url: str
    title: str
    authors: list[str]
    published_date: str
    journal: str
    doi: str
    summary: str
    # 途中で取得
    github_url: str
    # 最後のサマリーで取得
    main_contributions: str
    methodology: str
    experimental_setup: str
    limitations: str
    future_research_directions: str
