import json
import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.core.base import BaseSubgraph
from airas.features.create.create_method_subgraph.input_data import (
    create_method_subgraph_input_data,
)
from airas.features.create.create_method_subgraph.nodes.idea_generator import (
    idea_generator,
)
from airas.features.create.create_method_subgraph.nodes.refine_method import (
    refine_idea,
)
from airas.features.create.create_method_subgraph.nodes.research_value_judgement import (
    research_value_judgement,
)
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.research_study import ResearchStudy
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

create_method_timed = lambda f: time_node("create_method_subgraph")(f)  # noqa: E731


class CreateMethodLLMMapping(BaseModel):
    idea_generator: LLM_MODEL = DEFAULT_NODE_LLMS["idea_generator"]
    refine_idea: LLM_MODEL = DEFAULT_NODE_LLMS["refine_idea"]
    research_value_judgement: LLM_MODEL = DEFAULT_NODE_LLMS["research_value_judgement"]


class CreateMethodSubgraphInputState(TypedDict):
    research_topic: str
    research_study_list: list[ResearchStudy]


class CreateMethodSubgraphHiddenState(TypedDict):
    new_idea: str
    idea_history: list[dict[str, str]]
    judgement_reason: str
    judgement_result: bool


class CreateMethodSubgraphOutputState(TypedDict):
    new_method: ResearchHypothesis


class CreateMethodSubgraphState(
    CreateMethodSubgraphInputState,
    CreateMethodSubgraphHiddenState,
    CreateMethodSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class CreateMethodSubgraph(BaseSubgraph):
    InputState = CreateMethodSubgraphInputState
    OutputState = CreateMethodSubgraphOutputState

    def __init__(
        self,
        llm_mapping: CreateMethodLLMMapping | None = None,
        refine_iterations: int = 2,
    ):
        self.llm_mapping = llm_mapping or CreateMethodLLMMapping()
        self.refine_iterations = refine_iterations
        check_api_key(llm_api_key_check=True)

    @create_method_timed
    def _initialize(self, state: CreateMethodSubgraphState) -> dict:
        """Initialize the subgraph state with input data"""
        return {
            "idea_history": [],
        }

    @create_method_timed
    def _idea_generator(self, state: CreateMethodSubgraphState) -> dict:
        idea_history = state["idea_history"]
        new_idea = idea_generator(
            llm_name=self.llm_mapping.idea_generator,
            research_topic=state["research_topic"],
            research_study_list=state["research_study_list"],
            idea_history=idea_history,
        )
        return {"new_idea": new_idea}

    @create_method_timed
    def _refine_idea(self, state: CreateMethodSubgraphState) -> dict:
        new_idea = refine_idea(
            llm_name=self.llm_mapping.refine_idea,
            research_topic=state["research_topic"],
            new_idea=state["new_idea"],
            research_study_list=state["research_study_list"],
            idea_history=state["idea_history"],
            refine_iterations=self.refine_iterations,
        )
        return {
            "new_idea": new_idea,
        }

    @create_method_timed
    def _research_value_judgement(self, state: CreateMethodSubgraphState) -> dict:
        reason, judgement_result = research_value_judgement(
            llm_name=self.llm_mapping.research_value_judgement,
            research_topic=state["research_topic"],
            new_idea=state["new_idea"],
            research_study_list=state["research_study_list"],
        )
        return {
            "judgement_reason": reason,
            "judgement_result": judgement_result,
        }

    def _rerun_decision(self, state: CreateMethodSubgraphState) -> str:
        if state["judgement_result"]:
            return "pass"
        else:
            state["idea_history"].append(
                {
                    "new_idea": state["new_idea"],
                    "reason": state["judgement_reason"],
                }
            )
            return "regenerate"

    def _format_method(self, state: CreateMethodSubgraphState) -> dict:
        new_method = ResearchHypothesis(
            method=state["new_idea"],
        )
        return {"new_method": new_method}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(CreateMethodSubgraphState)
        graph_builder.add_node("initialize", self._initialize)
        graph_builder.add_node("idea_generator", self._idea_generator)
        graph_builder.add_node("refine_idea", self._refine_idea)
        graph_builder.add_node(
            "research_value_judgement", self._research_value_judgement
        )
        graph_builder.add_node("format_method", self._format_method)

        graph_builder.add_edge(START, "initialize")
        graph_builder.add_edge("initialize", "idea_generator")
        graph_builder.add_edge("idea_generator", "refine_idea")
        graph_builder.add_edge("refine_idea", "research_value_judgement")
        graph_builder.add_conditional_edges(
            "research_value_judgement",
            self._rerun_decision,
            {
                "pass": "format_method",
                "regenerate": "idea_generator",
            },
        )
        graph_builder.add_edge("format_method", END)
        return graph_builder.compile()


def main():
    input = create_method_subgraph_input_data
    result = CreateMethodSubgraph().run(input)
    print(f"result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running CreateMethodSubgraph: {e}")
        raise
