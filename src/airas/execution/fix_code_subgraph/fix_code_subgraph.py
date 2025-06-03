import json
import logging
import os
from typing import Literal

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.execution.executor_subgraph.prompt.llm_decide import (
    llm_decide_prompt,
)
from airas.execution.fix_code_subgraph.input_data import fix_code_subgraph_input_data
from airas.execution.fix_code_subgraph.nodes.fix_code_with_devin import (
    fix_code_with_devin,
)
from airas.execution.fix_code_subgraph.nodes.llm_decide import llm_decide
from airas.execution.push_code_subgraph.nodes.check_devin_completion import (
    check_devin_completion,
)
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

fix_code_timed = lambda f: time_node("fix_code_subgraph")(f)  # noqa: E731


class FixCodeSubgraphInputState(TypedDict):
    experiment_session_id: str
    output_text_data: str
    error_text_data: str
    executed_flag: Literal[True]


class FixCodeSubgraphHiddenState(TypedDict):
    judgment_result: bool


class FixCodeSubgraphOutputState(TypedDict):
    output_text_data: str
    push_completion: bool
    executed_flag: bool


class FixCodeSubgraphState(
    FixCodeSubgraphInputState,
    FixCodeSubgraphHiddenState,
    FixCodeSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class FixCodeSubgraph:
    def __init__(
        self,
    ):
        self.headers = {
            "Authorization": f"Bearer {os.getenv('DEVIN_API_KEY')}",
            "Content-Type": "application/json",
        }
        check_api_key(
            llm_api_key_check=True,
            devin_api_key_check=True,
            github_personal_access_token_check=True,
        )

    @fix_code_timed
    def _llm_decide_node(self, state: FixCodeSubgraphState) -> dict[str, bool]:
        if not state.get("executed_flag", True):
            raise ValueError("Invalid state: GitHub Actions workflow was not executed (expected executed_flag == True)")
        
        judgment_result = llm_decide(
            llm_name="o3-mini-2025-01-31",
            output_text_data=state["output_text_data"],
            error_text_data=state["error_text_data"],
            prompt_template=llm_decide_prompt, 
        )
        return {
            "judgment_result": judgment_result,
        }

    @fix_code_timed
    def _fix_code_with_devin_node(self, state: FixCodeSubgraphState) -> dict:
        success = fix_code_with_devin(
            headers=self.headers,
            session_id=state["experiment_session_id"],
            output_text_data=state["output_text_data"],
            error_text_data=state["error_text_data"],
        )
        if not success:
            logger.warning("`fix_code_with_devin` failed. Continuing with `executed_flag=False`")
        return {
            "executed_flag": False
        }
    
    @fix_code_timed
    def _check_devin_completion_node(self, state: FixCodeSubgraphState) -> dict[str, bool]:
        result = check_devin_completion(
            headers=self.headers,
            session_id=state["experiment_session_id"],
        )
        if result is None:
            return {"push_completion": False}
        return {"push_completion": True}
    
    def _route_fix_or_end(self, state: FixCodeSubgraphState) -> str:
        if state.get("judgment_result") is True:
            return "finish"
        return "fix_code_with_devin_node"


    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(FixCodeSubgraphState)
        graph_builder.add_node("llm_decide_node", self._llm_decide_node)
        graph_builder.add_node("fix_code_with_devin_node", self._fix_code_with_devin_node)
        graph_builder.add_node("check_devin_completion_node", self._check_devin_completion_node)
        

        graph_builder.add_edge(START, "llm_decide_node")
        graph_builder.add_conditional_edges(
            "llm_decide_node",
            self._route_fix_or_end,
            {
                "fix_code_with_devin_node": "fix_code_with_devin_node",
                "finish": END,
            },
        )
        graph_builder.add_edge("fix_code_with_devin_node", "check_devin_completion_node")
        graph_builder.add_edge("check_devin_completion_node", END)
        return graph_builder.compile()

    def run(
        self, 
        input: FixCodeSubgraphInputState, 
        config: dict | None = None
    ) -> FixCodeSubgraphOutputState:
        graph = self.build_graph()
        full_result = graph.invoke(input, config=config or {})
        output_keys = FixCodeSubgraphOutputState.__annotations__.keys()
        result = {k: full_result[k] for k in output_keys if k in full_result}
        return result


def main():
    input = fix_code_subgraph_input_data
    result = FixCodeSubgraph().run(input)
    print(f"result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running FixCodeSubgraph: {e}")
        raise
