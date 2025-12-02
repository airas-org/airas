import asyncio
import json
import logging

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.features.executors.nodes.read_run_ids import read_run_ids_from_repository
from airas.features.github.nodes.create_branch import create_branches_for_run_ids
from airas.features.github.nodes.dispatch_workflow import dispatch_workflow
from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubConfig
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("execute_full_experiment_subgraph")(f)  # noqa: E731


class ExecuteFullExperimentSubgraphInputState(TypedDict):
    github_config: GitHubConfig


class ExecuteFullExperimentSubgraphOutputState(ExecutionTimeState, total=False):
    all_dispatched: bool
    branch_creation_results: list[tuple[str, str, bool]]


class ExecuteFullExperimentSubgraphState(
    ExecuteFullExperimentSubgraphInputState,
    ExecuteFullExperimentSubgraphOutputState,
    total=False,
):
    run_ids: list[str]


class ExecuteFullExperimentSubgraph:
    def __init__(
        self,
        github_client: GithubClient,
        runner_label: str = "ubuntu-latest",
        workflow_file: str = "run_full_experiment_with_claude_code.yml",
    ):
        self.github_client = github_client
        self.runner_label = runner_label
        self.workflow_file = workflow_file

        check_api_key(github_personal_access_token_check=True)

    @record_execution_time
    async def _read_run_ids(
        self, state: ExecuteFullExperimentSubgraphState
    ) -> dict[str, list[str]]:
        run_ids = await read_run_ids_from_repository(
            self.github_client,
            state["github_config"],
        )
        return {"run_ids": run_ids}

    @record_execution_time
    async def _create_branches(
        self, state: ExecuteFullExperimentSubgraphState
    ) -> dict[str, list[tuple[str, str, bool]]]:
        if not (run_ids := state.get("run_ids")):
            logger.error("No run_ids found in state")
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
        runner_label_json = json.dumps([self.runner_label])
        logger.info(f"Dispatching full experiments on {len(successful_pairs)} branches")

        tasks = [
            dispatch_workflow(
                self.github_client,
                github_config.github_owner,
                github_config.repository_name,
                branch_name,
                self.workflow_file,
                {"runner_label": runner_label_json, "run_id": run_id},
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

        graph_builder.add_node("read_run_ids", self._read_run_ids)
        graph_builder.add_node("create_branches", self._create_branches)
        graph_builder.add_node(
            "dispatch_full_experiments", self._dispatch_full_experiments
        )

        graph_builder.add_edge(START, "read_run_ids")
        graph_builder.add_edge("read_run_ids", "create_branches")
        graph_builder.add_edge("create_branches", "dispatch_full_experiments")
        graph_builder.add_edge("dispatch_full_experiments", END)

        return graph_builder.compile()


async def main():
    from airas.core.container import container
    from airas.features.executors.execute_full_experiment_subgraph.input_data import (
        execute_full_experiment_subgraph_input_data,
    )

    container.wire(modules=[__name__])
    await container.init_resources()

    try:
        github_client = await container.github_client()
        result = (
            await ExecuteFullExperimentSubgraph(
                github_client=github_client,
            )
            .build_graph()
            .ainvoke(execute_full_experiment_subgraph_input_data)
        )
        print(f"result: {result}")
    finally:
        await container.shutdown_resources()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Error running ExecuteFullExperimentSubgraph: {e}")
        raise
