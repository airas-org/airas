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
from airas.features.analysis.analytic_subgraph.nodes.evaluate_experimental_design import (
    evaluate_experimental_design,
)
from airas.features.analysis.analytic_subgraph.nodes.evaluate_methods import (
    evaluate_methods,
)
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
    evaluate_experimental_design: LLM_MODEL = DEFAULT_NODE_LLMS[
        "evaluate_experimental_design"
    ]
    evaluate_methods: LLM_MODEL = DEFAULT_NODE_LLMS["evaluate_methods"]


class AnalyticSubgraphInputState(TypedDict, total=False):
    new_method: ResearchHypothesis
    github_repository_info: GitHubRepositoryInfo
    experiment_iteration: int  # TODO: This will be removed.
    hypothesis_versions: list[ResearchHypothesis]


class AnalyticSubgraphHiddenState(TypedDict): ...


class AnalyticSubgraphOutputState(TypedDict):
    new_method: ResearchHypothesis
    hypothesis_versions: list[ResearchHypothesis]


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
        max_design_iterations: int = 1,
        max_method_iterations: int = 1,
    ):
        self.max_design_iterations = max_design_iterations
        self.max_method_iterations = max_method_iterations
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
    def _initialize(self, state: AnalyticSubgraphState) -> dict:
        if not state.get("hypothesis_versions"):
            return {"hypothesis_versions": []}
        return {}

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

    @analytic_timed
    def _evaluate_experimental_design(self, state: AnalyticSubgraphState) -> dict:
        new_method = evaluate_experimental_design(
            llm_name=self.llm_mapping.evaluate_experimental_design,
            new_method=state["new_method"],
            github_repository_info=state["github_repository_info"],
        )

        hypothesis_versions = state.get("hypothesis_versions", [])
        hypothesis_versions.append(new_method.model_copy(deep=True))

        new_method.design_iteration_id += 1
        # NOTE: 'new_method.method' remains unchanged for the next iteration.
        new_method.experimental_design = None
        new_method.experiment_runs = None
        new_method.experimental_analysis = None

        return {
            "new_method": new_method,
            "hypothesis_versions": hypothesis_versions,
        }

    @analytic_timed
    def _evaluate_methods(self, state: AnalyticSubgraphState) -> dict:
        new_method = evaluate_methods(
            llm_name=self.llm_mapping.evaluate_experimental_design,
            new_method=state["new_method"],
            github_repository_info=state["github_repository_info"],
        )

        hypothesis_versions = state.get("hypothesis_versions", [])
        hypothesis_versions.append(new_method.model_copy(deep=True))

        new_method.method_iteration_id += 1
        new_method.method = ""
        new_method.experimental_design = None
        new_method.experiment_runs = None
        new_method.experimental_analysis = None
        # TODO: `CreateMethodSubgraph` supports `method_feedback`

        return {
            "new_method": new_method,
            "hypothesis_versions": hypothesis_versions,
        }

    def _should_iterate(self, state: AnalyticSubgraphState) -> str:
        new_method = state["new_method"]

        design_iteration = new_method.design_iteration_id
        method_iteration = new_method.method_iteration_id

        if design_iteration < self.max_design_iterations:
            logger.info(
                f"Decision: Design iteration needed (current: {design_iteration}, next: {design_iteration + 1}, max: {self.max_design_iterations})"
            )
            return "iterate_design"
        elif method_iteration < self.max_method_iterations:
            logger.info(
                f"Decision: Method iteration needed (current: {method_iteration}, next: {method_iteration + 1}, max: {self.max_method_iterations})"
            )
            return "iterate_method"
        else:
            logger.info(
                f"Decision: No iteration needed "
                f"(design: {design_iteration}/{self.max_design_iterations}, "
                f"method: {'disabled' if self.max_method_iterations == 0 else f'{method_iteration}/{self.max_method_iterations}'})"
            )
            return "no_iteration"

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(AnalyticSubgraphState)

        graph_builder.add_node("initialize", self._initialize)
        graph_builder.add_node("execute_evaluation", self._execute_evaluation)
        graph_builder.add_node(
            "retrieve_evaluation_artifacts", self._retrieve_evaluation_artifacts
        )
        graph_builder.add_node("analytic_node", self._analytic_node)
        graph_builder.add_node(
            "evaluate_experimental_design", self._evaluate_experimental_design
        )
        graph_builder.add_node("evaluate_methods", self._evaluate_methods)

        graph_builder.add_edge(START, "initialize")
        graph_builder.add_edge("initialize", "execute_evaluation")
        graph_builder.add_edge("execute_evaluation", "retrieve_evaluation_artifacts")
        graph_builder.add_edge("retrieve_evaluation_artifacts", "analytic_node")

        graph_builder.add_conditional_edges(
            "analytic_node",
            self._should_iterate,
            {
                "no_iteration": END,
                "iterate_design": "evaluate_experimental_design",
                "iterate_method": "evaluate_methods",
            },
        )

        graph_builder.add_edge("evaluate_experimental_design", END)
        graph_builder.add_edge("evaluate_methods", END)

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
