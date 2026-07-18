import json
import logging

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.llm_config import NodeLLMConfig, require_llm_mapping
from airas.core.logging_utils import setup_logging
from airas.core.types.github import GitHubActionsAgent, GitHubConfig
from airas.infra.github_client import GithubClient
from airas.usecases.github.nodes.dispatch_workflow import dispatch_workflow

setup_logging()
logger = logging.getLogger(__name__)


def record_execution_time(f):
    return time_node("dispatch_paper_reproduction_generate_subgraph")(f)


class DispatchPaperReproductionGenerateLLMMapping(BaseModel):
    dispatch_paper_reproduction_generate: NodeLLMConfig


class DispatchPaperReproductionGenerateSubgraphInputState(TypedDict):
    github_config: GitHubConfig
    paper_url: str
    instruction: str
    repo_url: str
    github_actions_agent: GitHubActionsAgent


class DispatchPaperReproductionGenerateSubgraphOutputState(ExecutionTimeState):
    dispatched: bool


class DispatchPaperReproductionGenerateSubgraphState(
    DispatchPaperReproductionGenerateSubgraphInputState,
    DispatchPaperReproductionGenerateSubgraphOutputState,
    total=False,
):
    pass


class DispatchPaperReproductionGenerateSubgraph:
    def __init__(
        self,
        github_client: GithubClient,
        runner_label: list[str] | None = None,
        workflow_file: str = "run_paper_reproduction_generate.yml",
        llm_mapping: DispatchPaperReproductionGenerateLLMMapping | None = None,
    ):
        self.github_client = github_client
        self.runner_label = runner_label or ["ubuntu-latest"]
        self.workflow_file = workflow_file
        self.llm_mapping = require_llm_mapping(llm_mapping)

    @record_execution_time
    async def _dispatch_paper_reproduction_generate(
        self, state: DispatchPaperReproductionGenerateSubgraphState
    ) -> dict[str, bool]:
        github_config = state["github_config"]
        github_actions_agent = state["github_actions_agent"]

        logger.info(
            f"Dispatching {self.workflow_file} on branch "
            f"'{github_config.branch_name}' with runner_label={self.runner_label}"
        )

        inputs: dict[str, str] = {
            "branch_name": github_config.branch_name,
            "paper_url": state["paper_url"],
            "repo_url": state["repo_url"],
            "instruction": state["instruction"],
            "github_actions_agent": github_actions_agent,
            "model_name": self.llm_mapping.dispatch_paper_reproduction_generate.llm_name,
            "runner_label": json.dumps(self.runner_label),
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
            logger.info(f"Dispatch successful: {self.workflow_file}")
        else:
            logger.error(f"Dispatch failed: {self.workflow_file}")

        return {"dispatched": success}

    def build_graph(self):
        graph_builder = StateGraph(
            DispatchPaperReproductionGenerateSubgraphState,
            input_schema=DispatchPaperReproductionGenerateSubgraphInputState,
            output_schema=DispatchPaperReproductionGenerateSubgraphOutputState,
        )
        graph_builder.add_node(
            "dispatch_paper_reproduction_generate",
            self._dispatch_paper_reproduction_generate,
        )
        graph_builder.add_edge(START, "dispatch_paper_reproduction_generate")
        graph_builder.add_edge("dispatch_paper_reproduction_generate", END)
        return graph_builder.compile()
