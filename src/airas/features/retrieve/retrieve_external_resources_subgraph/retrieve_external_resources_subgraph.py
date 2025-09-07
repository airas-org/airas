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
from airas.features.retrieve.retrieve_external_resources_subgraph.nodes.fetch_resource_details import (
    fetch_resource_details,
)
from airas.features.retrieve.retrieve_external_resources_subgraph.nodes.search_huggingface_resources import (
    search_huggingface_resources,
)
from airas.features.retrieve.retrieve_external_resources_subgraph.nodes.select_relevant_resources import (
    select_relevant_resources,
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
    select_relevant_resources: LLM_MODEL = DEFAULT_NODE_LLMS.get(
        "select_relevant_resources", "o3-2025-04-16"
    )


class RetrieveExternalResourcesInputState(TypedDict):
    new_method: ResearchHypothesis


class RetrieveExternalResourcesHiddenState(TypedDict):
    huggingface_search_results: dict[str, list[dict[str, str]]]
    selected_resources: dict[str, list[dict[str, str]]]


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

    @retrieve_external_resources_timed
    def _search_huggingface_resources(
        self, state: RetrieveExternalResourcesState
    ) -> dict:
        huggingface_search_results = search_huggingface_resources(
            new_method=state["new_method"]
        )
        return {"huggingface_search_results": huggingface_search_results}

    @retrieve_external_resources_timed
    def _select_relevant_resources(self, state: RetrieveExternalResourcesState) -> dict:
        selected_resources = select_relevant_resources(
            llm_name=self.llm_mapping.select_relevant_resources,
            new_method=state["new_method"],
            huggingface_search_results=state["huggingface_search_results"],
        )
        return {"selected_resources": selected_resources}

    @retrieve_external_resources_timed
    def _fetch_resource_details(self, state: RetrieveExternalResourcesState) -> dict:
        new_method = fetch_resource_details(
            new_method=state["new_method"],
            selected_resources=state["selected_resources"],
        )
        return {"new_method": new_method}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(RetrieveExternalResourcesState)
        graph_builder.add_node(
            "search_huggingface_resources", self._search_huggingface_resources
        )
        graph_builder.add_node(
            "select_relevant_resources", self._select_relevant_resources
        )
        graph_builder.add_node("fetch_resource_details", self._fetch_resource_details)

        # Build the pipeline: search -> select -> fetch
        graph_builder.add_edge(START, "search_huggingface_resources")
        graph_builder.add_edge(
            "search_huggingface_resources", "select_relevant_resources"
        )
        graph_builder.add_edge("select_relevant_resources", "fetch_resource_details")
        graph_builder.add_edge("fetch_resource_details", END)

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
