import logging

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.logging_utils import setup_logging
from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient
from airas.usecases.github.nodes.create_branch import create_branch

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("create_branch_subgraph")(f)  # noqa: E731


class CreateBranchSubgraphInputState(TypedDict):
    github_config: GitHubConfig


class CreateBranchSubgraphOutputState(ExecutionTimeState):
    new_github_config: GitHubConfig


class CreateBranchSubgraphState(
    CreateBranchSubgraphInputState,
    CreateBranchSubgraphOutputState,
    total=False,
):
    head_sha: str


class CreateBranchSubgraph:
    def __init__(
        self,
        github_client: GithubClient,
        new_branch_name: str,
    ):
        self.github_client = github_client
        self.new_branch_name = new_branch_name

    @record_execution_time
    async def _get_head_sha(self, state: CreateBranchSubgraphState) -> dict[str, str]:
        github_config = state["github_config"]
        logger.info(
            f"Getting HEAD SHA for branch '{github_config.branch_name}' "
            f"in '{github_config.github_owner}/{github_config.repository_name}'"
        )

        branch_info = await self.github_client.aget_branch(
            github_owner=github_config.github_owner,
            repository_name=github_config.repository_name,
            branch_name=github_config.branch_name,
        )
        if not branch_info:
            raise ValueError(
                f"Branch '{github_config.branch_name}' not found in "
                f"'{github_config.github_owner}/{github_config.repository_name}'"
            )

        head_sha = branch_info["commit"]["sha"]
        logger.info(f"HEAD SHA: {head_sha}")
        return {"head_sha": head_sha}

    @record_execution_time
    async def _create_branch(
        self, state: CreateBranchSubgraphState
    ) -> dict[str, GitHubConfig]:
        github_config = state["github_config"]
        logger.info(
            f"Creating branch '{self.new_branch_name}' from '{github_config.branch_name}'"
        )

        is_created = await create_branch(
            github_client=self.github_client,
            github_owner=github_config.github_owner,
            repository_name=github_config.repository_name,
            new_branch_name=self.new_branch_name,
            from_sha=state["head_sha"],
        )
        if not is_created:
            raise RuntimeError(f"Failed to create branch '{self.new_branch_name}'")

        new_github_config = GitHubConfig(
            github_owner=github_config.github_owner,
            repository_name=github_config.repository_name,
            branch_name=self.new_branch_name,
        )
        logger.info(f"Branch '{self.new_branch_name}' created successfully")
        return {"new_github_config": new_github_config}

    def build_graph(self):
        graph_builder = StateGraph(
            CreateBranchSubgraphState,
            input_schema=CreateBranchSubgraphInputState,
            output_schema=CreateBranchSubgraphOutputState,
        )

        graph_builder.add_node("get_head_sha", self._get_head_sha)
        graph_builder.add_node("create_branch", self._create_branch)

        graph_builder.add_edge(START, "get_head_sha")
        graph_builder.add_edge("get_head_sha", "create_branch")
        graph_builder.add_edge("create_branch", END)

        return graph_builder.compile()
