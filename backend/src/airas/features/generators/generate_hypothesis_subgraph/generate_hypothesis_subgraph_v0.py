import logging
from typing import cast

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.features.generators.generate_hypothesis_subgraph.nodes.evaluate_novelty_and_significance import (
    evaluate_novelty_and_significance,
)
from airas.features.generators.generate_hypothesis_subgraph.nodes.generate_hypothesis import (
    generate_hypothesis,
)
from airas.features.generators.generate_hypothesis_subgraph.nodes.refine_hypothesis import (
    refine_hypothesis,
)
from airas.services.api_client.langchain_client import LangChainClient
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
)
from airas.types.research_hypothesis import EvaluatedHypothesis, ResearchHypothesis
from airas.types.research_study import ResearchStudy
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("generate_hypothesis_subgraph")(f)  # noqa: E731


class GenerateHypothesisSubgraphV0LLMMapping(BaseModel):
    generate_hypothesis: LLM_MODEL = DEFAULT_NODE_LLMS["generate_hypothesis"]
    evaluate_novelty_and_significance: LLM_MODEL = DEFAULT_NODE_LLMS[
        "evaluate_novelty_and_significance"
    ]
    refine_hypothesis: LLM_MODEL = DEFAULT_NODE_LLMS["refine_hypothesis"]


class GenerateHypothesisSubgraphV0InputState(TypedDict):
    research_objective: str
    research_study_list: list[ResearchStudy]


class GenerateHypothesisSubgraphV0OutputState(TypedDict):
    research_hypothesis: ResearchHypothesis


class GenerateHypothesisSubgraphV0State(
    GenerateHypothesisSubgraphV0InputState,
    GenerateHypothesisSubgraphV0OutputState,
    ExecutionTimeState,
):
    refine_iterations: int
    evaluated_hypothesis_history: list[EvaluatedHypothesis]


class GenerateHypothesisSubgraphV0:
    def __init__(
        self,
        langchain_client: LangChainClient,
        llm_mapping: GenerateHypothesisSubgraphV0LLMMapping | None = None,
        refinement_rounds: int = 2,
    ):
        self.langchain_client = langchain_client
        self.llm_mapping = llm_mapping or GenerateHypothesisSubgraphV0LLMMapping()
        self.refinement_rounds = refinement_rounds
        check_api_key(llm_api_key_check=True)

    @recode_execution_time
    def _initialize(
        self, state: GenerateHypothesisSubgraphV0State
    ) -> dict[str, list[EvaluatedHypothesis] | int]:
        return {
            "evaluated_hypothesis_history": [],
            "refine_iterations": 0,
        }

    @recode_execution_time
    async def _generate_hypothesis(
        self, state: GenerateHypothesisSubgraphV0State
    ) -> dict[str, ResearchHypothesis]:
        research_hypothesis = await generate_hypothesis(
            llm_name=self.llm_mapping.generate_hypothesis,
            llm_client=self.langchain_client,
            research_objective=state["research_objective"],
            research_study_list=state["research_study_list"],
        )
        return {"research_hypothesis": research_hypothesis}

    @recode_execution_time
    async def _evaluate_novelty_and_significance(
        self, state: GenerateHypothesisSubgraphV0State
    ) -> dict[str, list[EvaluatedHypothesis]]:
        evaluated_hypothesis = await evaluate_novelty_and_significance(
            research_objective=state["research_objective"],
            research_study_list=state["research_study_list"],
            research_hypothesis=state["research_hypothesis"],
            llm_name=self.llm_mapping.evaluate_novelty_and_significance,
            llm_client=self.langchain_client,
        )
        return {
            "evaluated_hypothesis_history": state["evaluated_hypothesis_history"]
            + [evaluated_hypothesis],
        }

    def _should_refine_iteration(self, state: GenerateHypothesisSubgraphV0State) -> str:
        latest_hypothesis = state["evaluated_hypothesis_history"][-1]
        if (
            cast(int, latest_hypothesis.evaluation.novelty_score) >= 9
            and cast(int, latest_hypothesis.evaluation.significance_score) >= 9
        ):
            return "end"
        elif state["refine_iterations"] < self.refinement_rounds:
            return "regenerate"
        else:
            logger.info("Refinement iterations exceeded, passing.")
            return "end"

    @recode_execution_time
    async def _refine_hypothesis(
        self, state: GenerateHypothesisSubgraphV0State
    ) -> dict[str, ResearchHypothesis | int]:
        refined_hypothesis = await refine_hypothesis(
            llm_name=self.llm_mapping.refine_hypothesis,
            llm_client=self.langchain_client,
            research_objective=state["research_objective"],
            evaluated_hypothesis_history=state["evaluated_hypothesis_history"],
            research_study_list=state["research_study_list"],
        )
        return {
            "research_hypothesis": refined_hypothesis,
            "refine_iterations": state["refine_iterations"] + 1,
        }

    def _finalize_hypothesis(
        self, state: GenerateHypothesisSubgraphV0State
    ) -> dict[str, ResearchHypothesis]:
        return {
            "research_hypothesis": state["evaluated_hypothesis_history"][-1].hypothesis,
        }

    def build_graph(self):
        graph_builder = StateGraph(GenerateHypothesisSubgraphV0State)
        graph_builder.add_node("initialize", self._initialize)
        graph_builder.add_node("generate_hypothesis", self._generate_hypothesis)
        graph_builder.add_node(
            "evaluate_novelty_and_significance", self._evaluate_novelty_and_significance
        )
        graph_builder.add_node("refine_hypothesis", self._refine_hypothesis)
        graph_builder.add_node("finalize_hypothesis", self._finalize_hypothesis)

        graph_builder.add_edge(START, "initialize")
        graph_builder.add_edge("initialize", "generate_hypothesis")
        graph_builder.add_edge(
            "generate_hypothesis", "evaluate_novelty_and_significance"
        )
        graph_builder.add_conditional_edges(
            "evaluate_novelty_and_significance",
            self._should_refine_iteration,
            {
                "end": "finalize_hypothesis",
                "regenerate": "refine_hypothesis",
            },
        )
        graph_builder.add_edge("refine_hypothesis", "evaluate_novelty_and_significance")
        graph_builder.add_edge("finalize_hypothesis", END)
        return graph_builder.compile()
