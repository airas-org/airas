import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.core.base import BaseSubgraph
from airas.features.retrieve.retrieve_external_resources_subgraph.input_data import (
    retrieve_external_resources_subgraph_input_data,
)
from airas.features.retrieve.retrieve_external_resources_subgraph.nodes.search_huggingface_resources import (
    search_huggingface_resources,
)
from airas.features.retrieve.retrieve_external_resources_subgraph.nodes.select_external_resources import (
    select_external_resources,
)
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.types.research_hypothesis import ResearchHypothesis
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

retrieve_external_resources_str = "retrieve_external_resources_subgraph"


def retrieve_external_resources_timed(f):
    return time_node(retrieve_external_resources_str)(f)  # noqa: E731


class RetrieveExternalResourcesLLMMapping(BaseModel):
    select_external_resources: LLM_MODEL = DEFAULT_NODE_LLMS.get(
        "select_external_resources", "o3-2025-04-16"
    )


class RetrieveExternalResourcesInputState(TypedDict):
    new_method: ResearchHypothesis


class RetrieveExternalResourcesHiddenState(TypedDict):
    huggingface_search_results: dict[str, list[dict[str, str]]]


class RetrieveExternalResourcesOutputState(TypedDict):
    new_method: ResearchHypothesis


class RetrieveExternalResourcesState(
    RetrieveExternalResourcesInputState,
    RetrieveExternalResourcesHiddenState,
    RetrieveExternalResourcesOutputState,
    ExecutionTimeState,
):
    pass


class RetrieveExternalResourcesSubgraph(BaseSubgraph):
    InputState = RetrieveExternalResourcesInputState
    OutputState = RetrieveExternalResourcesOutputState

    def __init__(
        self,
        llm_mapping: dict[str, str] | RetrieveExternalResourcesLLMMapping | None = None,
        max_huggingface_results_per_search: int = 10,
    ):
        if llm_mapping is None:
            self.llm_mapping = RetrieveExternalResourcesLLMMapping()
        elif isinstance(llm_mapping, dict):
            try:
                self.llm_mapping = RetrieveExternalResourcesLLMMapping.model_validate(
                    llm_mapping
                )
            except Exception as e:
                raise TypeError(
                    f"Invalid llm_mapping values. Must contain valid LLM model names. Error: {e}"
                ) from e
        elif isinstance(llm_mapping, RetrieveExternalResourcesLLMMapping):
            self.llm_mapping = llm_mapping
        else:
            raise TypeError(
                f"llm_mapping must be None, dict[str, str], or RetrieveExternalResourcesLLMMapping, "
                f"but got {type(llm_mapping)}"
            )
        check_api_key()
        self.max_huggingface_results_per_search = max_huggingface_results_per_search

    async def _search_huggingface_resources(
        self, state: RetrieveExternalResourcesState
    ) -> dict[str, dict[str, list[dict[str, str]]]]:
        huggingface_search_results = await search_huggingface_resources(
            new_method=state["new_method"],
            max_results_per_search=self.max_huggingface_results_per_search,
        )
        return {"huggingface_search_results": huggingface_search_results}

    def _select_external_resources(self, state: RetrieveExternalResourcesState) -> dict:
        updated_method = select_external_resources(
            llm_name=self.llm_mapping.select_external_resources,
            new_method=state["new_method"],
            huggingface_search_results=state["huggingface_search_results"],
        )
        return {"new_method": updated_method}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(RetrieveExternalResourcesState)
        graph_builder.add_node(
            "search_huggingface_resources", self._search_huggingface_resources
        )
        graph_builder.add_node(
            "select_external_resources", self._select_external_resources
        )

        graph_builder.add_edge(START, "search_huggingface_resources")
        graph_builder.add_edge(
            "search_huggingface_resources", "select_external_resources"
        )
        graph_builder.add_edge("select_external_resources", END)

        return graph_builder.compile()


def main():
    input_data = retrieve_external_resources_subgraph_input_data
    result = RetrieveExternalResourcesSubgraph().run(input_data)
    print(f"result: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running RetrieveExternalResourcesSubgraph: {e}")
        raise
