import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.core.base import BaseSubgraph
from airas.features.evaluate.evaluate_experimental_consistency_subgraph.input_data import (
    evaluate_experimental_consistency_subgraph_input_data,
)
from airas.features.evaluate.evaluate_experimental_consistency_subgraph.nodes.evaluate_experimental_consistency import (
    evaluate_experimental_consistency,
)
from airas.features.evaluate.evaluate_experimental_consistency_subgraph.prompts.evaluate_experimental_consistency_prompt import (
    evaluate_experimental_consistency_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.types.research_hypothesis import ResearchHypothesis
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def evaluate_experimental_consistency_timed(f):
    return time_node("evaluate_experimental_consistency")(f)


class EvaluateExperimentalConsistencyLLMMapping(BaseModel):
    evaluate_experimental_consistency: LLM_MODEL = DEFAULT_NODE_LLMS[
        "evaluate_experimental_consistency"
    ]


class EvaluateExperimentalConsistencySubgraphInputState(TypedDict, total=False):
    new_method: ResearchHypothesis
    consistency_feedback: list[str]
    consistency_score: list[int]


class EvaluateExperimentalConsistencySubgraphHiddenState(TypedDict): ...


class EvaluateExperimentalConsistencySubgraphOutputState(TypedDict):
    is_experiment_consistent: bool
    consistency_feedback: list[str]
    consistency_score: list[int]


class EvaluateExperimentalConsistencySubgraphState(
    EvaluateExperimentalConsistencySubgraphInputState,
    EvaluateExperimentalConsistencySubgraphHiddenState,
    EvaluateExperimentalConsistencySubgraphOutputState,
    ExecutionTimeState,
):
    pass


class EvaluateExperimentalConsistencySubgraph(BaseSubgraph):
    InputState = EvaluateExperimentalConsistencySubgraphInputState
    OutputState = EvaluateExperimentalConsistencySubgraphOutputState

    def __init__(
        self,
        llm_mapping: dict[str, str]
        | EvaluateExperimentalConsistencyLLMMapping
        | None = None,
        prompt_template: str | None = None,
    ):
        if llm_mapping is None:
            self.llm_mapping = EvaluateExperimentalConsistencyLLMMapping()
        elif isinstance(llm_mapping, dict):
            self.llm_mapping = EvaluateExperimentalConsistencyLLMMapping(**llm_mapping)
        elif isinstance(llm_mapping, EvaluateExperimentalConsistencyLLMMapping):
            self.llm_mapping = llm_mapping
        else:
            raise TypeError(
                f"llm_mapping must be None, dict[str, str], or EvaluateExperimentalConsistencyLLMMapping, "
                f"but got {type(llm_mapping)}"
            )

        self.prompt_template = (
            prompt_template or evaluate_experimental_consistency_prompt
        )
        check_api_key(llm_api_key_check=True)

    @evaluate_experimental_consistency_timed
    def _evaluate_experimental_consistency(
        self, state: EvaluateExperimentalConsistencySubgraphState
    ) -> dict[str, ResearchHypothesis]:
        is_experiment_consistent, updated_feedback, updated_scores = (
            evaluate_experimental_consistency(
                llm_name=self.llm_mapping.evaluate_experimental_consistency,
                prompt_template=self.prompt_template,
                new_method=state["new_method"],
                existing_feedback=state.get("consistency_feedback"),
                existing_scores=state.get("consistency_score"),
            )
        )
        return {
            "is_experiment_consistent": is_experiment_consistent,
            "consistency_feedback": updated_feedback,
            "consistency_score": updated_scores,
        }

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(EvaluateExperimentalConsistencySubgraphState)
        graph_builder.add_node(
            "evaluate_experimental_consistency", self._evaluate_experimental_consistency
        )

        graph_builder.add_edge(START, "evaluate_experimental_consistency")
        graph_builder.add_edge("evaluate_experimental_consistency", END)
        return graph_builder.compile()


def main():
    input = evaluate_experimental_consistency_subgraph_input_data
    result = EvaluateExperimentalConsistencySubgraph().run(input)

    print(f"result: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running EvaluateExperimentalConsistencySubgraph: {e}")
        raise
