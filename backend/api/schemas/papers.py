from pydantic import BaseModel, Field

from airas.core.types.experiment_code import ExperimentCode
from airas.core.types.experimental_analysis import ExperimentalAnalysis
from airas.core.types.experimental_design import ExperimentalDesign
from airas.core.types.experimental_results import ExperimentalResults
from airas.core.types.paper import PaperContent, SearchMethod
from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.core.types.research_study import ResearchStudy
from airas.usecases.retrieve.retrieve_paper_subgraph.retrieve_paper_subgraph import (
    RetrievePaperSubgraphLLMMapping,
)
from airas.usecases.writers.write_subgraph.write_subgraph import WriteLLMMapping


class SearchPaperTitlesRequestBody(BaseModel):
    search_method: SearchMethod = "airas_db"
    queries: list[str]
    max_results_per_query: int = Field(default=3, gt=0)
    collection_name: str = "airas_papers_db"  # NOTE: collection_name is only used for qdrant; kept unified for simplicity despite ISP.


class SearchPaperTitlesResponseBody(BaseModel):
    paper_titles: list[str]
    execution_time: dict[str, list[float]]


class RetrievePaperSubgraphRequestBody(BaseModel):
    paper_titles: list[str]
    llm_mapping: RetrievePaperSubgraphLLMMapping | None = None


class RetrievePaperSubgraphResponseBody(BaseModel):
    research_study_list: list[ResearchStudy]
    execution_time: dict[str, list[float]]


class WriteSubgraphRequestBody(BaseModel):
    research_hypothesis: ResearchHypothesis
    experimental_design: ExperimentalDesign
    experiment_code: ExperimentCode
    experimental_results: ExperimentalResults
    experimental_analysis: ExperimentalAnalysis
    research_study_list: list[ResearchStudy]
    references_bib: str
    writing_refinement_rounds: int = 2
    llm_mapping: WriteLLMMapping | None = None


class WriteSubgraphResponseBody(BaseModel):
    paper_content: PaperContent
    execution_time: dict[str, list[float]]
