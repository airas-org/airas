import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.core.base import BaseSubgraph
from airas.features.review.check_experimental_results_subgraph.input_data import (
    check_experimental_results_subgraph_input_data,
)
from airas.features.review.check_experimental_results_subgraph.nodes.check_experimental_results import (
    check_experimental_results,
)
from airas.features.review.check_experimental_results_subgraph.prompts.check_experimental_results_prompt import (
    check_experimental_results_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.types.paper import PaperContent
from airas.types.research_hypothesis import ResearchHypothesis
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

check_experimental_results_timed = lambda f: time_node("check_experimental_results")(f)  # noqa: E731


class CheckExperimentalResultsLLMMapping(BaseModel):
    check_experimental_results: LLM_MODEL = DEFAULT_NODE_LLMS[
        "check_experimental_results"
    ]


class CheckExperimentalResultsSubgraphInputState(TypedDict):
    paper_content: PaperContent
    new_method: ResearchHypothesis


class CheckExperimentalResultsSubgraphHiddenState(TypedDict): ...


class CheckExperimentalResultsSubgraphOutputState(TypedDict):
    new_method: ResearchHypothesis


class CheckExperimentalResultsSubgraphState(
    CheckExperimentalResultsSubgraphInputState,
    CheckExperimentalResultsSubgraphHiddenState,
    CheckExperimentalResultsSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class CheckExperimentalResultsSubgraph(BaseSubgraph):
    InputState = CheckExperimentalResultsSubgraphInputState
    OutputState = CheckExperimentalResultsSubgraphOutputState

    def __init__(
        self,
        llm_mapping: dict[str, str] | CheckExperimentalResultsLLMMapping | None = None,
        prompt_template: str | None = None,
    ):
        if llm_mapping is None:
            self.llm_mapping = CheckExperimentalResultsLLMMapping()
        elif isinstance(llm_mapping, dict):
            self.llm_mapping = CheckExperimentalResultsLLMMapping(**llm_mapping)
        elif isinstance(llm_mapping, CheckExperimentalResultsLLMMapping):
            self.llm_mapping = llm_mapping
        else:
            raise TypeError(
                f"llm_mapping must be None, dict[str, str], or CheckExperimentalResultsLLMMapping, "
                f"but got {type(llm_mapping)}"
            )

        self.prompt_template = prompt_template or check_experimental_results_prompt
        check_api_key(llm_api_key_check=True)

    def _check_experimental_results(
        self, state: CheckExperimentalResultsSubgraphState
    ) -> dict[str, ResearchHypothesis]:
        new_method = check_experimental_results(
            llm_name=self.llm_mapping.check_experimental_results,
            prompt_template=self.prompt_template,
            paper_content=state["paper_content"],
            new_method=state["new_method"],
        )
        return {"new_method": new_method}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(CheckExperimentalResultsSubgraphState)
        graph_builder.add_node(
            "check_experimental_results", self._check_experimental_results
        )

        graph_builder.add_edge(START, "check_experimental_results")
        graph_builder.add_edge("check_experimental_results", END)
        return graph_builder.compile()


def main():
    input = check_experimental_results_subgraph_input_data
    result = CheckExperimentalResultsSubgraph().run(input)

    print(f"result: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running CheckExperimentalResultsSubgraph: {e}")
        raise
