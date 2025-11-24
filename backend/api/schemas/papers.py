from typing import Any

from pydantic import BaseModel


class RetrievePaperSubgraphRequestBody(BaseModel):
    query_list: list[str]
    max_results_per_query: int


class RetrievePaperSubgraphResponseBody(BaseModel):
    arxiv_info_list: list[list[Any]]
    execution_time: dict[str, dict[str, list[float]]]
