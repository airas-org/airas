from pydantic import BaseModel

from airas.features.writers.write_subgraph.write_subgraph import WriteLLMMapping
from airas.types.experiment_code import ExperimentCode
from airas.types.experimental_analysis import ExperimentalAnalysis
from airas.types.experimental_design import ExperimentalDesign
from airas.types.experimental_results import ExperimentalResults
from airas.types.paper import PaperContent
from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.research_study import ResearchStudy


class RetrievePaperSubgraphRequestBody(BaseModel):
    query_list: list[str]
    max_results_per_query: int


class RetrievePaperSubgraphResponseBody(BaseModel):
    research_study_list: list[list[ResearchStudy]]
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
    llm_mapping: WriteLLMMapping


class WriteSubgraphResponseBody(BaseModel):
    paper_content: PaperContent
    execution_time: dict[str, list[float]]
