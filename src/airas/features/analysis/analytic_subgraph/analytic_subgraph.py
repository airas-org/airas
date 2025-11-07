import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.core.base import BaseSubgraph
from airas.features.analysis.analytic_subgraph.nodes.analytic_node import analytic_node
from airas.features.analysis.analytic_subgraph.nodes.evaluate_method import (
    evaluate_method,
)
from airas.features.analysis.analytic_subgraph.nodes.select_best_iteration import (
    select_best_iteration,
)
from airas.features.execution.execute_experiment_subgraph.nodes.execute_experiment import (
    execute_evaluation,
)
from airas.features.execution.execute_experiment_subgraph.nodes.retrieve_artifacts import (
    retrieve_evaluation_artifacts,
)
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_iteration import ExperimentEvaluation
from airas.types.research_session import ResearchSession
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

analytic_timed = lambda f: time_node("analytic_subgraph")(f)  # noqa: E731


class AnalyticLLMMapping(BaseModel):
    analytic_node: LLM_MODEL = DEFAULT_NODE_LLMS["analytic_node"]
    evaluate_method: LLM_MODEL = DEFAULT_NODE_LLMS["evaluate_method"]


class AnalyticSubgraphInputState(TypedDict, total=False):
    research_session: ResearchSession
    github_repository_info: GitHubRepositoryInfo


class AnalyticSubgraphHiddenState(TypedDict): ...


class AnalyticSubgraphOutputState(TypedDict):
    research_session: ResearchSession


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
    async def _execute_evaluation(
        self, state: AnalyticSubgraphState
    ) -> dict[str, bool]:
        success = await execute_evaluation(
            github_repository=state["github_repository_info"],
            research_session=state["research_session"],
        )
        return {"executed_flag": success}

    @analytic_timed
    async def _retrieve_evaluation_artifacts(
        self, state: AnalyticSubgraphState
    ) -> dict[str, ResearchSession]:
        research_session = await retrieve_evaluation_artifacts(
            github_repository=state["github_repository_info"],
            research_session=state["research_session"],
        )
        return {"research_session": research_session}

    @analytic_timed
    def _analytic_node(
        self, state: AnalyticSubgraphState
    ) -> dict[str, ResearchSession]:
        research_session = state["research_session"]
        analysis_report = analytic_node(
            llm_name=self.llm_mapping.analytic_node,
            research_session=research_session,
            github_repository_info=state["github_repository_info"],
        )
        research_session.current_iteration.experimental_analysis.analysis_report = (
            analysis_report
        )
        return {"research_session": research_session}

    @analytic_timed
    def _evaluate_method(
        self, state: AnalyticSubgraphState
    ) -> dict[str, ResearchSession]:
        research_session = state["research_session"]
        method_feedback = evaluate_method(
            llm_name=self.llm_mapping.evaluate_method,
            research_session=research_session,
            github_repository_info=state["github_repository_info"],
        )
        if not research_session.current_iteration.experimental_analysis.evaluation:
            research_session.current_iteration.experimental_analysis.evaluation = (
                ExperimentEvaluation()
            )
        research_session.current_iteration.experimental_analysis.evaluation.method_feedback = method_feedback

        return {"research_session": research_session}

    @analytic_timed
    def _select_best_iteration(
        self, state: AnalyticSubgraphState
    ) -> dict[str, ResearchSession]:
        research_session = select_best_iteration(state["research_session"])
        return {"research_session": research_session}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(AnalyticSubgraphState)

        graph_builder.add_node("execute_evaluation", self._execute_evaluation)
        graph_builder.add_node(
            "retrieve_evaluation_artifacts", self._retrieve_evaluation_artifacts
        )
        graph_builder.add_node("analytic_node", self._analytic_node)
        graph_builder.add_node("evaluate_method", self._evaluate_method)
        graph_builder.add_node("select_best_iteration", self._select_best_iteration)

        graph_builder.add_edge(START, "execute_evaluation")
        graph_builder.add_edge("execute_evaluation", "retrieve_evaluation_artifacts")
        graph_builder.add_edge("retrieve_evaluation_artifacts", "analytic_node")
        graph_builder.add_edge("analytic_node", "evaluate_method")
        graph_builder.add_edge("evaluate_method", "select_best_iteration")
        graph_builder.add_edge("select_best_iteration", END)

        return graph_builder.compile()


def main():
    from airas.features.analysis.analytic_subgraph.input_data import (
        analytic_subgraph_input_data,
    )
    from airas.services.api_client.api_clients_container import sync_container

    sync_container.wire(modules=[__name__])
    input = analytic_subgraph_input_data
    result = AnalyticSubgraph().run(input)

    print(f"result: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running AnalyticSubgraph: {e}")
        raise
