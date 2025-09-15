import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.core.base import BaseSubgraph
from airas.features.retrieve.retrieve_hugging_face_subgraph.input_data import (
    retrieve_hugging_face_subgraph_input_data,
)
from airas.features.retrieve.retrieve_hugging_face_subgraph.nodes.search_hugging_face import (
    search_hugging_face,
)
from airas.features.retrieve.retrieve_hugging_face_subgraph.nodes.select_resources import (
    select_resources,
)
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.types.hugging_face import HuggingFace
from airas.types.research_hypothesis import ResearchHypothesis
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

retrieve_hugging_face_str = "retrieve_hugging_face_subgraph"


def retrieve_hugging_face_timed(f):
    return time_node(retrieve_hugging_face_str)(f)  # noqa: E731


class RetrieveHuggingFaceLLMMapping(BaseModel):
    select_resources: LLM_MODEL = DEFAULT_NODE_LLMS["select_resources"]


class RetrieveHuggingFaceInputState(TypedDict):
    new_method: ResearchHypothesis


class RetrieveHuggingFaceHiddenState(TypedDict):
    huggingface_search_results: HuggingFace


class RetrieveHuggingFaceOutputState(TypedDict):
    new_method: ResearchHypothesis


class RetrieveHuggingFaceState(
    RetrieveHuggingFaceInputState,
    RetrieveHuggingFaceHiddenState,
    RetrieveHuggingFaceOutputState,
    ExecutionTimeState,
):
    pass


class RetrieveHuggingFaceSubgraph(BaseSubgraph):
    InputState = RetrieveHuggingFaceInputState
    OutputState = RetrieveHuggingFaceOutputState

    def __init__(
        self,
        llm_mapping: dict[str, str] | RetrieveHuggingFaceLLMMapping | None = None,
        include_gated: bool = False,
        max_results_per_search: int = 10,
        max_models: int = 10,
        max_datasets: int = 10,
    ):
        self.max_results_per_search = max_results_per_search
        self.max_models = max_models
        self.max_datasets = max_datasets
        if llm_mapping is None:
            self.llm_mapping = RetrieveHuggingFaceLLMMapping()
        elif isinstance(llm_mapping, dict):
            try:
                self.llm_mapping = RetrieveHuggingFaceLLMMapping.model_validate(
                    llm_mapping
                )
            except Exception as e:
                raise TypeError(
                    f"Invalid llm_mapping values. Must contain valid LLM model names. Error: {e}"
                ) from e
        elif isinstance(llm_mapping, RetrieveHuggingFaceLLMMapping):
            self.llm_mapping = llm_mapping
        else:
            raise TypeError(
                f"llm_mapping must be None, dict[str, str], or RetrieveHuggingFaceLLMMapping, "
                f"but got {type(llm_mapping)}"
            )
        self.include_gated = include_gated
        check_api_key()

    async def _search_hugging_face(
        self, state: RetrieveHuggingFaceState
    ) -> dict[str, HuggingFace]:
        huggingface_search_results = await search_hugging_face(
            new_method=state["new_method"],
            max_results_per_search=self.max_results_per_search,
            include_gated=self.include_gated,
        )
        return {"huggingface_search_results": huggingface_search_results}

    def _select_resources(
        self, state: RetrieveHuggingFaceState
    ) -> dict[str, ResearchHypothesis]:
        updated_method = select_resources(
            llm_name=self.llm_mapping.select_resources,
            new_method=state["new_method"],
            huggingface_search_results=state["huggingface_search_results"],
            max_models=self.max_models,
            max_datasets=self.max_datasets,
        )
        return {"new_method": updated_method}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(RetrieveHuggingFaceState)
        graph_builder.add_node("search_hugging_face", self._search_hugging_face)
        graph_builder.add_node("select_resources", self._select_resources)

        graph_builder.add_edge(START, "search_hugging_face")
        graph_builder.add_edge("search_hugging_face", "select_resources")
        graph_builder.add_edge("select_resources", END)

        return graph_builder.compile()


def main():
    input_data = retrieve_hugging_face_subgraph_input_data
    result = RetrieveHuggingFaceSubgraph().run(input_data)
    print(f"result: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running RetrieveHuggingFaceSubgraph: {e}")
        raise
