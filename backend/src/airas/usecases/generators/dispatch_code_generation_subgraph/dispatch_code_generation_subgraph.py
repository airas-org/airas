import logging

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.llm_config import DEFAULT_NODE_LLM_CONFIG, NodeLLMConfig
from airas.core.logging_utils import setup_logging
from airas.core.types.experimental_design import ExperimentalDesign
from airas.core.types.github import GitHubActionsAgent, GitHubConfig
from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.core.types.wandb import WandbConfig
from airas.infra.github_client import GithubClient
from airas.usecases.github.nodes.dispatch_workflow import dispatch_workflow

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("dispatch_code_generation_subgraph")(f)  # noqa: E731


class DispatchCodeGenerationLLMMapping(BaseModel):
    dispatch_code_generation: NodeLLMConfig = DEFAULT_NODE_LLM_CONFIG[
        "dispatch_code_generation"
    ]


class DispatchCodeGenerationSubgraphInputState(TypedDict):
    github_config: GitHubConfig
    research_topic: str
    research_hypothesis: ResearchHypothesis
    experimental_design: ExperimentalDesign
    wandb_config: WandbConfig
    github_actions_agent: GitHubActionsAgent


class DispatchCodeGenerationSubgraphOutputState(ExecutionTimeState):
    dispatched: bool


class DispatchCodeGenerationSubgraphState(
    DispatchCodeGenerationSubgraphInputState,
    DispatchCodeGenerationSubgraphOutputState,
    total=False,
):
    pass


class DispatchCodeGenerationSubgraph:
    def __init__(
        self,
        github_client: GithubClient,
        workflow_file: str = "run_code_generator.yml",
        llm_mapping: DispatchCodeGenerationLLMMapping | None = None,
    ):
        self.github_client = github_client
        self.workflow_file = workflow_file
        self.llm_mapping = llm_mapping or DispatchCodeGenerationLLMMapping()

    @record_execution_time
    async def _dispatch_code_generation(
        self, state: DispatchCodeGenerationSubgraphState
    ) -> dict[str, bool]:
        github_config = state["github_config"]
        research_topic = state["research_topic"]
        research_hypothesis = state["research_hypothesis"]
        experimental_design = state["experimental_design"]
        wandb_config = state["wandb_config"]
        github_actions_agent = state["github_actions_agent"]

        logger.info(
            f"Dispatching code generation on branch '{github_config.branch_name}'"
        )

        inputs = {
            "branch_name": github_config.branch_name,
            "research_topic": research_topic,
            "research_hypothesis": research_hypothesis.model_dump_json(),
            "experimental_design": experimental_design.model_dump_json(),
            "wandb_config": wandb_config.model_dump_json(),
            "github_actions_agent": github_actions_agent,
            "model_name": self.llm_mapping.dispatch_code_generation.llm_name,
        }

        success = await dispatch_workflow(
            self.github_client,
            github_config.github_owner,
            github_config.repository_name,
            github_config.branch_name,
            self.workflow_file,
            inputs,
        )

        if success:
            logger.info("Code generation dispatch successful")
        else:
            logger.error("Code generation dispatch failed")

        return {"dispatched": success}

    def build_graph(self):
        graph_builder = StateGraph(
            DispatchCodeGenerationSubgraphState,
            input_schema=DispatchCodeGenerationSubgraphInputState,
            output_schema=DispatchCodeGenerationSubgraphOutputState,
        )

        graph_builder.add_node(
            "dispatch_code_generation", self._dispatch_code_generation
        )

        graph_builder.add_edge(START, "dispatch_code_generation")
        graph_builder.add_edge("dispatch_code_generation", END)

        return graph_builder.compile()
