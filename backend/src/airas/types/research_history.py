from typing import Any, Optional

from pydantic import BaseModel, Field

from airas.types.experiment_code import ExperimentCode
from airas.types.experimental_analysis import ExperimentalAnalysis
from airas.types.experimental_design import ExperimentalDesign
from airas.types.experimental_results import ExperimentalResults
from airas.types.paper import PaperContent, PaperReviewScores
from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.research_study import ResearchStudy


class ResearchHistory(BaseModel):
    # --- Project Management ---
    research_objective: Optional[str] = Field(
        None, description="Main research objective or topic"
    )

    # --- Search & Investigation ---
    query_list: Optional[list[str]] = Field(
        None, description="List of search queries used for paper retrieval"
    )
    research_study_list: Optional[list[ResearchStudy]] = Field(
        None, description="List of main research studies analyzed"
    )

    # --- Hypothesis & Experimentation ---
    research_hypothesis: Optional[ResearchHypothesis] = Field(
        None, description="Research hypothesis generated"
    )
    experimental_design: Optional[ExperimentalDesign] = Field(
        None, description="Experimental design and methodology"
    )
    experiment_code: Optional[ExperimentCode] = Field(
        None, description="Generated experiment code and implementation"
    )
    experiment_results: Optional[ExperimentalResults] = Field(
        None, description="Results from running experiments"
    )
    experimental_analysis: Optional[ExperimentalAnalysis] = Field(
        None, description="Analysis and interpretation of experimental results"
    )

    # --- Writing & Publication ---
    paper_content: Optional[PaperContent] = Field(
        None, description="Generated paper content including sections and text"
    )
    references_bib: Optional[str] = Field(
        None, description="Bibliography references in BibTeX format"
    )
    latex_text: Optional[str] = Field(None, description="LaTeX formatted paper text")
    paper_url: Optional[str] = Field(
        None, description="URL to the published or hosted paper"
    )
    full_html: Optional[str] = Field(
        None, description="Full HTML content of the generated paper"
    )
    github_pages_url: Optional[str] = Field(
        None, description="GitHub Pages URL for the published paper"
    )
    paper_review_scores: Optional[PaperReviewScores] = Field(
        None, description="Review scores and feedback for the paper"
    )

    # --- Miscellaneous ---
    additional_data: Optional[dict[str, Any]] = Field(
        None, description="Additional data fields for future extensions"
    )
