import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.core.base import BaseSubgraph
from airas.features.analysis.analytic_subgraph.input_data import (
    analytic_subgraph_input_data,
)
from airas.features.analysis.analytic_subgraph.nodes.analytic_node import analytic_node
from airas.features.execution.execute_experiment_subgraph.nodes.execute_experiment import (
    execute_evaluation,
)
from airas.features.execution.execute_experiment_subgraph.nodes.retrieve_artifacts import (
    retrieve_evaluation_artifacts,
)
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import ResearchHypothesis
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

analytic_timed = lambda f: time_node("analytic_subgraph")(f)  # noqa: E731


class AnalyticLLMMapping(BaseModel):
    analytic_node: LLM_MODEL = DEFAULT_NODE_LLMS["analytic_node"]


class AnalyticSubgraphInputState(TypedDict):
    new_method: ResearchHypothesis
    github_repository_info: GitHubRepositoryInfo
    experiment_iteration: int


class AnalyticSubgraphHiddenState(TypedDict): ...


class AnalyticSubgraphOutputState(TypedDict):
    new_method: ResearchHypothesis


class AnalyticSubgraphState(
    AnalyticSubgraphInputState,
    AnalyticSubgraphHiddenState,
    AnalyticSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class AnalyticSubgraph(BaseSubgraph):
    InputState = AnalyticSubgraphInputState
    OutputState = AnalyticSubgraphOutputState

    def __init__(
        self,
        llm_mapping: dict[str, str] | AnalyticLLMMapping | None = None,
    ):
        if llm_mapping is None:
            self.llm_mapping = AnalyticLLMMapping()
        elif isinstance(llm_mapping, dict):
            try:
                self.llm_mapping = AnalyticLLMMapping.model_validate(llm_mapping)
            except Exception as e:
                raise TypeError(
                    f"Invalid llm_mapping values. Must contain valid LLM model names. Error: {e}"
                ) from e
        elif isinstance(llm_mapping, AnalyticLLMMapping):
            self.llm_mapping = llm_mapping
        else:
            raise TypeError(
                f"llm_mapping must be None, dict[str, str], or AnalyticLLMMapping, "
                f"but got {type(llm_mapping)}"
            )
        check_api_key(llm_api_key_check=True)

    @analytic_timed
    def _execute_evaluation(self, state: AnalyticSubgraphState) -> dict:
        execute_evaluation(
            github_repository=state["github_repository_info"],
            experiment_iteration=state["experiment_iteration"],
            new_method=state["new_method"],
        )
        return {}

    @analytic_timed
    def _retrieve_evaluation_artifacts(self, state: AnalyticSubgraphState) -> dict:
        new_method = retrieve_evaluation_artifacts(
            github_repository=state["github_repository_info"],
            experiment_iteration=state["experiment_iteration"],
            new_method=state["new_method"],
        )
        return {"new_method": new_method}

    @analytic_timed
    def _analytic_node(self, state: AnalyticSubgraphState) -> dict:
        new_method = analytic_node(
            llm_name=self.llm_mapping.analytic_node,
            new_method=state["new_method"],
            github_repository_info=state["github_repository_info"],
        )
        return {"new_method": new_method}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(AnalyticSubgraphState)
        graph_builder.add_node("execute_evaluation", self._execute_evaluation)
        graph_builder.add_node(
            "retrieve_evaluation_artifacts", self._retrieve_evaluation_artifacts
        )
        graph_builder.add_node("analytic_node", self._analytic_node)

        graph_builder.add_edge(START, "execute_evaluation")
        graph_builder.add_edge("execute_evaluation", "retrieve_evaluation_artifacts")
        graph_builder.add_edge("retrieve_evaluation_artifacts", "analytic_node")
        graph_builder.add_edge("analytic_node", END)
        return graph_builder.compile()


def main():
    input = analytic_subgraph_input_data

    result = AnalyticSubgraph().run(input)

    print(f"result: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running AnalyticSubgraph: {e}")
        raise
