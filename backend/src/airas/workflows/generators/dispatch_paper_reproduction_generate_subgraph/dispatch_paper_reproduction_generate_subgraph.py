from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.llm_config import NodeLLMConfig, require_llm_mapping
from airas.core.types.github import GitHubActionsAgent, GitHubConfig
from airas.infra.github_client import GithubClient
from airas.usecases.reproduction.dispatch_paper_reproduction_generate import (
    WORKFLOW_FILE,
    dispatch_paper_reproduction_generate,
)


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
    repro_id: str


class DispatchPaperReproductionGenerateSubgraphState(
    DispatchPaperReproductionGenerateSubgraphInputState,
    DispatchPaperReproductionGenerateSubgraphOutputState,
    total=False,
):
    pass


class DispatchPaperReproductionGenerateSubgraph:
    """`dispatch_paper_reproduction_generate` as one graph node."""

    def __init__(
        self,
        github_client: GithubClient,
        runner_label: list[str] | None = None,
        workflow_file: str = WORKFLOW_FILE,
        llm_mapping: DispatchPaperReproductionGenerateLLMMapping | None = None,
    ):
        self.github_client = github_client
        self.runner_label = runner_label
        self.workflow_file = workflow_file
        self.llm_mapping = require_llm_mapping(llm_mapping)

    @time_node("dispatch_paper_reproduction_generate_subgraph")
    async def _dispatch(
        self, state: DispatchPaperReproductionGenerateSubgraphState
    ) -> dict:
        return await dispatch_paper_reproduction_generate(
            self.github_client,
            state["github_config"],
            state["paper_url"],
            state["instruction"],
            self.llm_mapping.dispatch_paper_reproduction_generate.llm_name,
            repo_url=state["repo_url"],
            github_actions_agent=state["github_actions_agent"],
            runner_label=self.runner_label,
            workflow_file=self.workflow_file,
        )

    def build_graph(self):
        graph_builder = StateGraph(
            DispatchPaperReproductionGenerateSubgraphState,
            input_schema=DispatchPaperReproductionGenerateSubgraphInputState,
            output_schema=DispatchPaperReproductionGenerateSubgraphOutputState,
        )
        graph_builder.add_node("dispatch_paper_reproduction_generate", self._dispatch)
        graph_builder.add_edge(START, "dispatch_paper_reproduction_generate")
        graph_builder.add_edge("dispatch_paper_reproduction_generate", END)
        return graph_builder.compile()
