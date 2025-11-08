import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.core.base import BaseSubgraph
from airas.features.create.create_method_subgraph.nodes.improve_method import (
    improve_method,
)
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_iteration import ResearchIteration
from airas.types.research_session import ResearchSession
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

create_method_timed = lambda f: time_node("create_method_subgraph")(f)  # noqa: E731


class CreateMethodLLMMapping(BaseModel):
    improve_method: LLM_MODEL = DEFAULT_NODE_LLMS["improve_method"]


class CreateMethodSubgraphInputState(TypedDict):
    research_session: ResearchSession
    github_repository_info: GitHubRepositoryInfo


class CreateMethodSubgraphHiddenState(TypedDict): ...


class CreateMethodSubgraphOutputState(TypedDict):
    research_session: ResearchSession


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
        llm_mapping: dict[str, str] | CreateMethodLLMMapping | None = None,
    ):
        if llm_mapping is None:
            self.llm_mapping = CreateMethodLLMMapping()
        elif isinstance(llm_mapping, dict):
            try:
                self.llm_mapping = CreateMethodLLMMapping.model_validate(llm_mapping)
            except Exception as e:
                raise TypeError(
                    f"Invalid llm_mapping values. Must contain valid LLM model names. Error: {e}"
                ) from e
        elif isinstance(llm_mapping, CreateMethodLLMMapping):
            self.llm_mapping = llm_mapping
        else:
            raise TypeError(
                f"llm_mapping must be None, dict[str, str], or CreateMethodLLMMapping, "
                f"but got {type(llm_mapping)}"
            )
        check_api_key(llm_api_key_check=True)

    def _is_initial_creation(self, state: CreateMethodSubgraphState) -> str:
        iterations = state["research_session"].iterations
        if not iterations or len(iterations) == 0:
            return "initialize_method"
        return "improve_method"

    @create_method_timed
    def _initialize_method(
        self, state: CreateMethodSubgraphState
    ) -> dict[str, ResearchSession]:
        research_session = state["research_session"]
        if not (hypothesis := state["research_session"].hypothesis):
            raise ValueError(
                "ResearchSession must have a hypothesis for initialization."
            )

        research_session.iterations.append(
            ResearchIteration(
                method=hypothesis.method,
            )
        )

        return {"research_session": research_session}

    @create_method_timed
    def _improve_method(
        self, state: CreateMethodSubgraphState
    ) -> dict[str, ResearchSession]:
        research_session = state["research_session"]
        research_session.iterations.append(
            ResearchIteration(
                method=improve_method(
                    research_session=state["research_session"],
                    llm_name=self.llm_mapping.improve_method,
                    github_repository_info=state["github_repository_info"],
                ),
            )
        )
        return {"research_session": research_session}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(CreateMethodSubgraphState)

        graph_builder.add_node("initialize_method", self._initialize_method)
        graph_builder.add_node("improve_method", self._improve_method)

        graph_builder.add_conditional_edges(
            START,
            self._is_initial_creation,
            {
                "initialize_method": "initialize_method",
                "improve_method": "improve_method",
            },
        )

        graph_builder.add_edge("initialize_method", END)
        graph_builder.add_edge("improve_method", END)

        return graph_builder.compile()


def main():
    from airas.features.create.create_method_subgraph.input_data import (
        create_method_subgraph_input_data,
    )
    from airas.services.api_client.api_clients_container import sync_container
    sync_container.wire(modules=[__name__])
    input = create_method_subgraph_input_data

    result = CreateMethodSubgraph().run(input)
    print(f"result: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running CreateMethodSubgraph: {e}")
        raise
