import logging

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.logging_utils import setup_logging
from airas.core.types.experimental_design import DatasetSubfield
from airas.usecases.retrieve.retrieve_datasets_subgraph.nodes.retrieve_datasets import (
    retrieve_datasets,
)

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("retrieve_models_subgraph")(f)  # noqa: E731


class RetrieveDatasetsSubgraphInputState(TypedDict):
    dataset_subfield: DatasetSubfield


class RetrieveDatasetsSubgraphOutputState(ExecutionTimeState):
    datasets_dict: dict


class RetrieveDatasetsSubgraphState(
    RetrieveDatasetsSubgraphInputState,
    RetrieveDatasetsSubgraphOutputState,
):
    pass


class RetrieveDatasetsSubgraph:
    def __init__(
        self,
    ):
        pass

    @record_execution_time
    def _retrieve_datasets(self, state: RetrieveDatasetsSubgraphState) -> dict:
        datasets_dict = retrieve_datasets(
            dataset_subfield=state["dataset_subfield"],
        )
        return {"datasets_dict": datasets_dict}

    def build_graph(self):
        graph_builder = StateGraph(
            RetrieveDatasetsSubgraphState,
            input_schema=RetrieveDatasetsSubgraphInputState,
            output_schema=RetrieveDatasetsSubgraphOutputState,
        )
        graph_builder.add_node("retrieve_datasets", self._retrieve_datasets)

        graph_builder.add_edge(START, "retrieve_datasets")
        graph_builder.add_edge("retrieve_datasets", END)
        return graph_builder.compile()
