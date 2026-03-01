import logging

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.llm_config import DEFAULT_NODE_LLM_CONFIG, NodeLLMConfig
from airas.core.logging_utils import setup_logging
from airas.core.types.github import GitHubActionsAgent, GitHubConfig
from airas.infra.github_client import GithubClient
from airas.usecases.github.nodes.dispatch_workflow import dispatch_workflow

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("dispatch_diagram_generation_subgraph")(f)  # noqa: E731


class DispatchDiagramGenerationLLMMapping(BaseModel):
    dispatch_diagram_generation: NodeLLMConfig = DEFAULT_NODE_LLM_CONFIG[
        "dispatch_diagram_generation"
    ]


class DispatchDiagramGenerationSubgraphInputState(TypedDict):
    github_config: GitHubConfig
    github_actions_agent: GitHubActionsAgent


class DispatchDiagramGenerationSubgraphOutputState(ExecutionTimeState):
    dispatched: bool


class DispatchDiagramGenerationSubgraphState(
    DispatchDiagramGenerationSubgraphInputState,
    DispatchDiagramGenerationSubgraphOutputState,
    total=False,
):
    pass


class DispatchDiagramGenerationSubgraph:
    def __init__(
        self,
        github_client: GithubClient,
        workflow_file: str = "run_diagram_generator.yml",
        diagram_description: str | None = None,
        prompt_path: str | None = None,
        llm_mapping: DispatchDiagramGenerationLLMMapping | None = None,
    ):
        self.github_client = github_client
        self.workflow_file = workflow_file
        self.diagram_description = diagram_description
        self.prompt_path = prompt_path
        self.llm_mapping = llm_mapping or DispatchDiagramGenerationLLMMapping()

    @record_execution_time
    async def _dispatch_diagram_generation(
        self, state: DispatchDiagramGenerationSubgraphState
    ) -> dict[str, bool]:
        github_config = state["github_config"]
        github_actions_agent = state["github_actions_agent"]

        logger.info(
            f"Dispatching diagram generation on branch '{github_config.branch_name}'"
        )

        inputs: dict[str, str] = {
            "branch_name": github_config.branch_name,
            "github_actions_agent": github_actions_agent,
            "model_name": self.llm_mapping.dispatch_diagram_generation.llm_name,
        }

        if self.diagram_description is not None:
            inputs["diagram_description"] = self.diagram_description
        if self.prompt_path is not None:
            inputs["prompt_path"] = self.prompt_path

        success = await dispatch_workflow(
            self.github_client,
            github_config.github_owner,
            github_config.repository_name,
            github_config.branch_name,
            self.workflow_file,
            inputs,
        )

        if success:
            logger.info("Diagram generation dispatch successful")
        else:
            logger.error("Diagram generation dispatch failed")

        return {"dispatched": success}

    def build_graph(self):
        graph_builder = StateGraph(
            DispatchDiagramGenerationSubgraphState,
            input_schema=DispatchDiagramGenerationSubgraphInputState,
            output_schema=DispatchDiagramGenerationSubgraphOutputState,
        )

        graph_builder.add_node(
            "dispatch_diagram_generation", self._dispatch_diagram_generation
        )

        graph_builder.add_edge(START, "dispatch_diagram_generation")
        graph_builder.add_edge("dispatch_diagram_generation", END)

        return graph_builder.compile()
