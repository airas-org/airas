from enum import Enum

from pydantic import BaseModel, Field

from airas.features.retrieve.retrieve_paper_subgraph.retrieve_paper_subgraph import (
    RetrievePaperSubgraphLLMMapping,
)
from airas.features.writers.write_subgraph.write_subgraph import WriteLLMMapping
from airas.types.experiment_code import ExperimentCode
from airas.types.experimental_analysis import ExperimentalAnalysis
from airas.types.experimental_design import ExperimentalDesign
from airas.types.experimental_results import ExperimentalResults
from airas.types.paper import PaperContent
from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.research_study import ResearchStudy


class SearchMethod(str, Enum):
    AIRAS_DB = "airas_db"


class SearchPaperTitlesRequestBody(BaseModel):
    queries: list[str]
    max_results_per_query: int = Field(default=3, gt=0)
    search_method: SearchMethod = SearchMethod.AIRAS_DB


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
