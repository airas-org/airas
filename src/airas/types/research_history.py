from typing import Any, Optional

from pydantic import BaseModel, Field

from airas.types.github import GitHubRepositoryInfo
from airas.types.paper import PaperContent, PaperReviewScores
from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.research_idea import ResearchIdea
from airas.types.research_study import ResearchStudy


class ResearchHistory(BaseModel):
    github_repository_info: Optional[GitHubRepositoryInfo] = Field(
        None, description="GitHub repository information"
    )

    research_topic: Optional[str] = Field(None, description="Main research topic")
    queries: Optional[list[str]] = Field(None, description="Search queries used")

    research_study_list: Optional[list[ResearchStudy]] = Field(
        None, description="Main research studies"
    )
    reference_research_study_list: Optional[list[ResearchStudy]] = Field(
        None, description="Reference research studies"
    )
    new_method: Optional[ResearchHypothesis] = Field(
        None, description="Proposed new research method"
    )
    idea_info_history: Optional[list[ResearchIdea]] = Field(
        None, description="new research method history"
    )
    push_completion: Optional[bool] = Field(None, description="Push completion status")
    executed_flag: Optional[bool] = Field(None, description="Execution completion flag")

    experiment_iteration: Optional[int] = Field(
        None, description="Current experiment iteration"
    )

    paper_content: Optional[PaperContent] = Field(
        None, description="Generated paper content"
    )
    references_bib: Optional[str] = Field(None, description="Bibliography references")

    latex_text: Optional[str] = Field(None, description="LaTeX formatted text")
    full_html: Optional[str] = Field(None, description="Full HTML content")
    github_pages_url: Optional[str] = Field(None, description="GitHub Pages URL")
    readme_upload_result: Optional[bool] = Field(
        None, description="README upload success status"
    )

    paper_review_scores: Optional[PaperReviewScores] = Field(
        None, description="Review scores from ReviewPaperSubgraph"
    )

    additional_data: Optional[dict[str, Any]] = Field(
        None, description="Additional data fields for future extensions"
    )
