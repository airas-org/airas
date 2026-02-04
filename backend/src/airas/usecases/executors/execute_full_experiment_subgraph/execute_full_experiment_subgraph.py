import asyncio
import json
import logging

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.llm_config import DEFAULT_NODE_LLM_CONFIG, NodeLLMConfig
from airas.core.logging_utils import setup_logging
from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient
from airas.usecases.github.nodes.create_branch import create_branches_for_run_ids
from airas.usecases.github.nodes.dispatch_workflow import dispatch_workflow

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("execute_full_experiment_subgraph")(f)  # noqa: E731


class ExecuteFullExperimentLLMMapping(BaseModel):
    dispatch_full_experiments: NodeLLMConfig = DEFAULT_NODE_LLM_CONFIG[
        "dispatch_full_experiments"
    ]


class ExecuteFullExperimentSubgraphInputState(TypedDict):
    github_config: GitHubConfig
    run_ids: list[str]


class ExecuteFullExperimentSubgraphOutputState(ExecutionTimeState):
    all_dispatched: bool
    branch_creation_results: list[tuple[str, str, bool]]


class ExecuteFullExperimentSubgraphState(
    ExecuteFullExperimentSubgraphInputState,
    ExecuteFullExperimentSubgraphOutputState,
    total=False,
):
    pass


class ExecuteFullExperimentSubgraph:
    def __init__(
        self,
        github_client: GithubClient,
        runner_label: list[str] | None = None,
        workflow_file: str = "run_full_experiment.yml",
        github_actions_agent: str = "claude_code",
        llm_mapping: ExecuteFullExperimentLLMMapping | None = None,
    ):
        self.github_client = github_client
        self.runner_label = runner_label or ["ubuntu-latest"]
        self.workflow_file = workflow_file
        self.github_actions_agent = github_actions_agent
        self.llm_mapping = llm_mapping or ExecuteFullExperimentLLMMapping()

    @record_execution_time
    async def _create_branches(
        self, state: ExecuteFullExperimentSubgraphState
    ) -> dict[str, list[tuple[str, str, bool]]]:
        if not (run_ids := state["run_ids"]):
            logger.error("run_ids list is empty")
            return {"branch_creation_results": []}

        github_config = state["github_config"]
        logger.info(f"Creating branches for {len(run_ids)} run_ids")

        branch_results = await create_branches_for_run_ids(
            self.github_client,
            github_config,
            run_ids,
        )

        successful_count = sum(1 for _, _, success in branch_results if success)

        if successful_count == 0:
            logger.error("No branches were created successfully")
        else:
            logger.info(
                f"Successfully created {successful_count} out of {len(run_ids)} branches"
            )

        return {"branch_creation_results": branch_results}

    @record_execution_time
    async def _dispatch_full_experiments(
        self, state: ExecuteFullExperimentSubgraphState
    ) -> dict[str, bool]:
        if not (branch_creation_results := state.get("branch_creation_results")):
            logger.error("No branch_creation_results found in state")
            return {"all_dispatched": False}

        successful_pairs = [
            (run_id, branch_name)
            for run_id, branch_name, success in branch_creation_results
            if success
        ]

        if not successful_pairs:
            logger.error("No successful branches to dispatch workflows")
            return {"all_dispatched": False}

        github_config = state["github_config"]
        runner_label_json = json.dumps(self.runner_label)
        logger.info(f"Dispatching full experiments on {len(successful_pairs)} branches")

        tasks = [
            dispatch_workflow(
                self.github_client,
                github_config.github_owner,
                github_config.repository_name,
                branch_name,
                self.workflow_file,
                {
                    "branch_name": branch_name,
                    "runner_label": runner_label_json,
                    "run_id": run_id,
                    "github_actions_agent": self.github_actions_agent,
                    "model_name": self.llm_mapping.dispatch_full_experiments.llm_name,
                },
            )
            for run_id, branch_name in successful_pairs
        ]

        results = await asyncio.gather(*tasks)

        failed_count = 0
        for (run_id, _), success in zip(successful_pairs, results, strict=True):
            if success:
                logger.info(
                    f"Full experiment dispatch successful for run_id '{run_id}'"
                )
            else:
                logger.error(f"Full experiment dispatch failed for run_id '{run_id}'")
                failed_count += 1

        if failed_count > 0:
            logger.error(
                f"{failed_count} out of {len(successful_pairs)} experiment dispatches failed"
            )
            return {"all_dispatched": False}

        logger.info(
            f"All {len(successful_pairs)} full experiment dispatches completed successfully"
        )
        return {"all_dispatched": True}

    def build_graph(self):
        graph_builder = StateGraph(
            ExecuteFullExperimentSubgraphState,
            input_schema=ExecuteFullExperimentSubgraphInputState,
            output_schema=ExecuteFullExperimentSubgraphOutputState,
        )

        graph_builder.add_node("create_branches", self._create_branches)
        graph_builder.add_node(
            "dispatch_full_experiments", self._dispatch_full_experiments
        )

        graph_builder.add_edge(START, "create_branches")
        graph_builder.add_edge("create_branches", "dispatch_full_experiments")
        graph_builder.add_edge("dispatch_full_experiments", END)

        return graph_builder.compile()
