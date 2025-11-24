from pydantic import BaseModel

from airas.features.retrieve.summarize_paper_subgraph.nodes.summarize_paper import (
    LLMOutput,
)


class RetrievePaperSubgraphRequestBody(BaseModel):
    query_list: list[str]
    max_results_per_query: int


class RetrievePaperSubgraphResponseBody(BaseModel):
    arxiv_full_text_list: list[list[str]]
    arxiv_summary_list: list[list[LLMOutput]]
    github_code_list: list[list[str]]
    execution_time: dict[str, dict[str, list[float]]]
