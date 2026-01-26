import logging

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.logging_utils import setup_logging
from airas.core.types.experimental_design import ModelSubfield
from airas.usecases.retrieve.retrieve_models_subgraph.nodes.retrieve_models import (
    retrieve_models,
)

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("retrieve_models_subgraph")(f)  # noqa: E731


class RetrieveModelsSubgraphInputState(TypedDict):
    model_subfield: ModelSubfield


class RetrieveModelsSubgraphOutputState(ExecutionTimeState):
    models_dict: dict


class RetrieveModelsSubgraphState(
    RetrieveModelsSubgraphInputState,
    RetrieveModelsSubgraphOutputState,
):
    pass


class RetrieveModelsSubgraph:
    def __init__(
        self,
    ):
        pass

    @record_execution_time
    def _retrieve_models(self, state: RetrieveModelsSubgraphState) -> dict:
        models_dict = retrieve_models(
            model_subfield=state["model_subfield"],
        )
        return {"models_dict": models_dict}

    def build_graph(self):
        graph_builder = StateGraph(
            RetrieveModelsSubgraphState,
            input_schema=RetrieveModelsSubgraphInputState,
            output_schema=RetrieveModelsSubgraphOutputState,
        )
        graph_builder.add_node("retrieve_models", self._retrieve_models)

        graph_builder.add_edge(START, "retrieve_models")
        graph_builder.add_edge("retrieve_models", END)
        return graph_builder.compile()
