import json
import logging
import os
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.execution.push_code_subgraph.nodes.check_devin_completion import (
    check_devin_completion,
)
from airas.execution.push_code_subgraph.nodes.push_code_with_devin import (
    push_code_with_devin,
)
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

push_code_timed = lambda f: time_node("push_code_subgraph")(f)  # noqa: E731


class PushCodeSubgraphInputState(TypedDict):
    new_method: str
    experiment_code: str
    github_repository: str
    branch_name: str


class PushCodeSubgraphHiddenState(TypedDict):
    ...
    

class PushCodeSubgraphOutputState(TypedDict):
    push_completion: bool
    experiment_session_id: str
    experiment_devin_url: str
    experiment_iteration: int


class PushCodeSubgraphState(
    PushCodeSubgraphInputState,
    PushCodeSubgraphHiddenState,
    PushCodeSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class PushCodeSubgraph:
    def __init__(
        self,
    ):
        self.headers = {
            "Authorization": f"Bearer {os.getenv('DEVIN_API_KEY')}",
            "Content-Type": "application/json",
        }
        check_api_key(
            devin_api_key_check=True,
            github_personal_access_token_check=True,
        )

    @push_code_timed
    def _init_state(self, state: PushCodeSubgraphState) -> dict[str, int]:
        logger.info("---PushCodeSubgraph---")
        return {"experiment_iteration": 1}
      
    @push_code_timed
    def _push_code_with_devin_node(self, state: PushCodeSubgraphState) -> dict[str, str]:
        experiment_session_id, experiment_devin_url = push_code_with_devin(
            headers=self.headers,
            github_repository=state["github_repository"],
            branch_name=state["branch_name"],
            new_method=state["new_method"],
            experiment_code=state["experiment_code"],
            experiment_iteration=state["experiment_iteration"],
        )
        return {
            "experiment_session_id": experiment_session_id,
            "experiment_devin_url": experiment_devin_url,
        }

    @push_code_timed
    def _check_devin_completion_node(self, state: PushCodeSubgraphState) -> dict[str, bool]:
        result = check_devin_completion(
            headers=self.headers,
            session_id=state["experiment_session_id"],
        )
        if result is None:
            return {"push_completion": False}
        return {"push_completion": True}


    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(PushCodeSubgraphState)
        graph_builder.add_node("init_state", self._init_state)
        graph_builder.add_node("push_code_with_devin_node", self._push_code_with_devin_node)
        graph_builder.add_node("check_devin_completion_node", self._check_devin_completion_node)

        graph_builder.add_edge(START, "init_state")
        graph_builder.add_edge("init_state", "push_code_with_devin_node")
        graph_builder.add_edge("push_code_with_devin_node", "check_devin_completion_node")
        graph_builder.add_edge("check_devin_completion_node", END)
        return graph_builder.compile()
    
    def run(
        self, 
        state: dict[str, Any], 
        config: dict | None = None
    ) -> dict[str, Any]:
        input_state_keys = PushCodeSubgraphInputState.__annotations__.keys()
        output_state_keys = PushCodeSubgraphOutputState.__annotations__.keys()

        input_state = {k: state[k] for k in input_state_keys if k in state}
        result = self.build_graph().invoke(input_state, config=config or {})
        output_state = {k: result[k] for k in output_state_keys if k in result}

        cleaned_state = {k: v for k, v in state.items() if k != "subgraph_name"}

        return {
            "subgraph_name": self.__class__.__name__,
            **cleaned_state,
            **output_state, 
        }


def main():
    input = PushCodeSubgraphInputState(
        new_method="example_method",
        experiment_code="print('Hello, world!')",
        github_repository="fuyu-quant/airas-temp",
        branch_name="main",
    )
    result = PushCodeSubgraph().run(input)
    print(f"result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running PushCodeSubgraph: {e}")
        raise
