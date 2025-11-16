import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.core.base import BaseSubgraph
from airas.features.evaluate.evaluate_paper_results_subgraph.input_data import (
    evaluate_paper_results_subgraph_input_data,
)
from airas.features.evaluate.evaluate_paper_results_subgraph.nodes.evaluate_paper_results import (
    evaluate_paper_results,
)
from airas.features.evaluate.evaluate_paper_results_subgraph.prompts.evaluate_paper_results_prompt import (
    evaluate_paper_results_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.types.github import GitHubRepositoryInfo
from airas.types.paper import PaperContent
from airas.types.research_hypothesis import ResearchHypothesis
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

evaluate_paper_results_timed = lambda f: time_node("evaluate_paper_results")(f)  # noqa: E731


class EvaluatePaperResultsLLMMapping(BaseModel):
    evaluate_paper_results: LLM_MODEL = DEFAULT_NODE_LLMS["evaluate_paper_results"]


class EvaluatePaperResultsSubgraphInputState(TypedDict):
    paper_content: PaperContent
    new_method: ResearchHypothesis
    github_repository_info: GitHubRepositoryInfo


class EvaluatePaperResultsSubgraphHiddenState(TypedDict): ...


class EvaluatePaperResultsSubgraphOutputState(TypedDict):
    was_experiment_executed: bool
    is_better_than_baseline: bool


class EvaluatePaperResultsSubgraphState(
    EvaluatePaperResultsSubgraphInputState,
    EvaluatePaperResultsSubgraphHiddenState,
    EvaluatePaperResultsSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class EvaluatePaperResultsSubgraph(BaseSubgraph):
    InputState = EvaluatePaperResultsSubgraphInputState
    OutputState = EvaluatePaperResultsSubgraphOutputState

    def __init__(
        self,
        llm_mapping: dict[str, str] | EvaluatePaperResultsLLMMapping | None = None,
        prompt_template: str | None = None,
    ):
        if llm_mapping is None:
            self.llm_mapping = EvaluatePaperResultsLLMMapping()
        elif isinstance(llm_mapping, dict):
            self.llm_mapping = EvaluatePaperResultsLLMMapping(**llm_mapping)
        elif isinstance(llm_mapping, EvaluatePaperResultsLLMMapping):
            self.llm_mapping = llm_mapping
        else:
            raise TypeError(
                f"llm_mapping must be None, dict[str, str], or EvaluatePaperResultsLLMMapping, "
                f"but got {type(llm_mapping)}"
            )

        self.prompt_template = prompt_template or evaluate_paper_results_prompt
        check_api_key(llm_api_key_check=True)

    @evaluate_paper_results_timed
    def _evaluate_paper_results(
        self, state: EvaluatePaperResultsSubgraphState
    ) -> dict[str, bool]:
        was_experiment_executed, is_better_than_baseline = evaluate_paper_results(
            llm_name=self.llm_mapping.evaluate_paper_results,
            prompt_template=self.prompt_template,
            paper_content=state["paper_content"],
            github_repository_info=state["github_repository_info"],
        )
        return {
            "was_experiment_executed": was_experiment_executed,
            "is_better_than_baseline": is_better_than_baseline,
        }

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(EvaluatePaperResultsSubgraphState)
        graph_builder.add_node("evaluate_paper_results", self._evaluate_paper_results)

        graph_builder.add_edge(START, "evaluate_paper_results")
        graph_builder.add_edge("evaluate_paper_results", END)
        return graph_builder.compile()


def main():
    input = evaluate_paper_results_subgraph_input_data
    result = EvaluatePaperResultsSubgraph().run(input)

    print(f"result: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running EvaluatePaperResultsSubgraph: {e}")
        raise
