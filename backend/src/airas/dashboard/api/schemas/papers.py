from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from airas.core.types.experiment_code import ExperimentCode
from airas.core.types.experiment_history import ExperimentHistory
from airas.core.types.paper import PaperContent, SearchMethod
from airas.core.types.paper_search import PAPER_SEARCH_SOURCES, PaperSearchResult
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


# Sources that support semantic (AI-embedding) search natively.
SEMANTIC_SEARCH_SOURCES = ("openalex",)


class SearchPapersRequestBody(BaseModel):
    query: str
    sources: list[str] = Field(default_factory=lambda: list(PAPER_SEARCH_SOURCES))
    max_results_per_source: int = Field(default=5, gt=0, le=50)
    year: str | None = None
    search_mode: Literal["keyword", "semantic"] = "keyword"

    @field_validator("sources")
    @classmethod
    def _validate_sources(cls, sources: list[str]) -> list[str]:
        unknown = sorted(set(sources) - set(PAPER_SEARCH_SOURCES))
        if unknown:
            raise ValueError(
                f"Unknown sources: {', '.join(unknown)}. "
                f"Available: {', '.join(PAPER_SEARCH_SOURCES)}"
            )
        if not sources:
            raise ValueError("At least one source must be selected")
        return sources

    @model_validator(mode="after")
    def _validate_semantic_sources(self) -> "SearchPapersRequestBody":
        if self.search_mode == "semantic":
            unsupported = sorted(set(self.sources) - set(SEMANTIC_SEARCH_SOURCES))
            if unsupported:
                raise ValueError(
                    f"Semantic search is not supported by: {', '.join(unsupported)}. "
                    f"Semantic-capable sources: {', '.join(SEMANTIC_SEARCH_SOURCES)}"
                )
        return self


class SearchPapersResponseBody(BaseModel):
    papers: list[PaperSearchResult]
    source_results: dict[str, int]
    search_errors: dict[str, str]
    execution_time: dict[str, list[float]]


class FetchPaperFulltextRequestBody(BaseModel):
    # Exactly one identifier is enough; they are tried in this order.
    arxiv_id: str | None = None
    doi: str | None = None
    pdf_url: str | None = None


class FetchPaperFulltextResponseBody(BaseModel):
    text: str
    status: Literal["fulltext", "abstract_only", "not_found"]
    resolved_from: str | None
    execution_time: dict[str, list[float]]


class RetrievePaperSubgraphRequestBody(BaseModel):
    paper_titles: list[str]
    llm_mapping: RetrievePaperSubgraphLLMMapping | None = None


class RetrievePaperSubgraphResponseBody(BaseModel):
    research_study_list: list[ResearchStudy]
    execution_time: dict[str, list[float]]


class WriteSubgraphRequestBody(BaseModel):
    research_hypothesis: ResearchHypothesis
    experiment_history: ExperimentHistory
    experiment_code: ExperimentCode
    research_study_list: list[ResearchStudy]
    references_bib: str
    writing_refinement_rounds: int = 2
    llm_mapping: WriteLLMMapping | None = None


class WriteSubgraphResponseBody(BaseModel):
    paper_content: PaperContent
    execution_time: dict[str, list[float]]
