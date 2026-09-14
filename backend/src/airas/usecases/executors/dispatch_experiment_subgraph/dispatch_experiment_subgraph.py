import json
import logging
import re
import shlex
from typing import Literal

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.logging_utils import setup_logging
from airas.core.types.experiment_history import RunStage
from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient
from airas.infra.seyval_client import SeyvalClient

setup_logging()
logger = logging.getLogger(__name__)

Backend = Literal["github_actions", "seyval"]

EXPERIMENT_WORKFLOW_FILE = "run_experiment.yml"

RUN_COMMAND_TEMPLATE = "make run RUN_ID={run_id} MODE={mode}"
# What the Makefile accepts for RUN_ID (it names a results directory and a
# config file): letters, digits, '_', '.' and '-', not starting with '.'.
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-][A-Za-z0-9_.-]*$")


def check_run_id(run_id: str) -> str:
    if not RUN_ID_PATTERN.match(run_id):
        raise ValueError(
            f"run_id {run_id!r} may hold only letters, digits, '_', '.' and '-', "
            "and may not start with '.'"
        )
    return run_id


def run_command(run_id: str, mode: str) -> str:
    """The argv element `bash -c` executes on Seyval. The run id is checked
    above and quoted here, so a value cannot carry a second command."""
    return RUN_COMMAND_TEMPLATE.format(
        run_id=shlex.quote(check_run_id(run_id)), mode=shlex.quote(mode)
    )


ANALYSIS_ACTIVE = ("pending", "running")


def record_execution_time(f):
    return time_node("dispatch_experiment_subgraph")(f)  # noqa: E731


class DispatchExperimentSubgraphInputState(TypedDict):
    github_config: GitHubConfig
    run_id: str


class DispatchExperimentSubgraphOutputState(ExecutionTimeState):
    dispatched: bool
    execution_id: str | None
    execution_url: str | None


class DispatchExperimentSubgraphState(
    DispatchExperimentSubgraphInputState,
    DispatchExperimentSubgraphOutputState,
    total=False,
):
    pass


class DispatchExperimentSubgraph:
    """Start one run on the chosen backend. The code must already be pushed;
    outputs stay on the backend until `import_run_outputs` copies them."""

    # TODO: 匂う。backend ごとに前提が違う引数を 1 つの署名で受けていて、
    # 無関係な方(github_actions に compute_id など)は黙って無視される。

    def __init__(
        self,
        backend: Backend,
        github_client: GithubClient,
        seyval_client: SeyvalClient | None = None,
        run_stage: RunStage | None = None,
        # github_actions
        runner_label: list[str] | None = None,
        # seyval
        compute_id: str | None = None,
        compute_type: str = "gpu-a10",
        inputs_from_runs: list[str] | None = None,
        time_limit: str | None = None,
        resource_count: int | None = None,
        user_dockerfile_path: str | None = "Dockerfile",
        command_args: list[str] | None = None,
        workspace_id: str | None = None,
    ):
        if backend == "seyval" and seyval_client is None:
            raise ValueError('backend="seyval" needs a seyval_client')
        self.backend = backend
        self.github_client = github_client
        self.seyval_client = seyval_client
        self.run_stage = run_stage or RunStage.SANITY
        self.runner_label = runner_label or ["ubuntu-latest"]
        self.compute_id = compute_id
        self.compute_type = compute_type
        self.inputs_from_runs = inputs_from_runs
        self.time_limit = time_limit
        self.resource_count = resource_count
        self.user_dockerfile_path = user_dockerfile_path
        self.command_args = command_args
        self.workspace_id = workspace_id

    @record_execution_time
    async def _dispatch(
        self, state: DispatchExperimentSubgraphState
    ) -> dict[str, bool | str | None]:
        github_config = state["github_config"]
        run_id = check_run_id(state["run_id"])
        if self.backend == "seyval":
            return await self._on_seyval(github_config, run_id)
        return await self._on_github_actions(github_config, run_id)

    async def _on_github_actions(
        self, github_config: GitHubConfig, run_id: str
    ) -> dict[str, bool | str | None]:
        inputs = {
            "branch_name": github_config.branch_name,
            "run_id": run_id,
            "runner_label": json.dumps(self.runner_label),
            "mode": self.run_stage.value,
        }
        logger.info(
            f"Dispatching {EXPERIMENT_WORKFLOW_FILE} for run_id={run_id} on branch "
            f"'{github_config.branch_name}' with runner_label={self.runner_label}"
        )
        response = await self.github_client.acreate_workflow_dispatch(
            github_config.github_owner,
            github_config.repository_name,
            EXPERIMENT_WORKFLOW_FILE,
            ref=github_config.branch_name,
            inputs=inputs,
            return_run_details=True,
        )
        details = response if isinstance(response, dict) else {}
        workflow_run_id = details.get("workflow_run_id")
        return {
            "dispatched": bool(response),
            "execution_id": str(workflow_run_id)
            if workflow_run_id is not None
            else None,
            "execution_url": details.get("html_url"),
        }

    async def _on_seyval(
        self, github_config: GitHubConfig, run_id: str
    ) -> dict[str, bool | str | None]:
        assert self.seyval_client is not None
        client = self.seyval_client
        git_url = (
            f"https://github.com/{github_config.github_owner}/"
            f"{github_config.repository_name}"
        )

        repository = await client.aregister_repository(
            git_url, workspace_id=self.workspace_id
        )
        repository_id = repository["id"]

        pulled = await client.apull_repository(repository_id)
        branch = next(
            (
                b
                for b in pulled.get("branches", [])
                if b.get("name") == github_config.branch_name
            ),
            None,
        )
        if branch is None:
            raise ValueError(
                f"Branch '{github_config.branch_name}' not found in {git_url}. "
                "Push the experiment code before dispatching."
            )
        commit_hash = branch["commit_hash"]
        analysis_id, experiment_id = await self._analyzed(
            repository_id, commit_hash, github_config.branch_name
        )
        mode = self.run_stage.value

        logger.info(
            f"Starting Seyval run for run_id={run_id} (mode={mode}, "
            f"compute_id={self.compute_id}, compute_type={self.compute_type}) "
            f"at commit {commit_hash[:12]}"
        )
        run = await client.astart_run(
            repository_id,
            commit_hash,
            experiment_id,
            analysis_id,
            compute_type=self.compute_type,
            compute_id=self.compute_id,
            inputs_from_runs=self.inputs_from_runs,
            time_limit=self.time_limit,
            resource_count=self.resource_count,
            user_dockerfile_path=self.user_dockerfile_path,
            command_args=self.command_args or ["bash", "-c", run_command(run_id, mode)],
        )
        return {
            "dispatched": True,
            "execution_id": str(run["run_id"]),
            "execution_url": run.get("run_url") or None,
        }

    async def _analyzed(
        self, repository_id: str, commit_hash: str, branch: str
    ) -> tuple[str, str]:
        """(analysis_id, experiment_id) for the commit. Registration analyzes
        the default branch HEAD by itself; any other commit is started here.
        Analysis takes minutes, so an unfinished one is reported for a retry
        rather than waited for inside the tool call."""
        assert self.seyval_client is not None
        client = self.seyval_client
        try:
            analysis = await client.aget_analysis(repository_id, commit_hash)
        except Exception:
            await client.astart_analysis(repository_id, commit_hash, branch=branch)
            analysis = await client.aget_analysis(repository_id, commit_hash)
        status = analysis.get("status")
        if status in ANALYSIS_ACTIVE:
            raise ValueError(
                f"Seyval is still analyzing commit {commit_hash[:12]} "
                f"(status: {status}); it takes a few minutes — call "
                "dispatch_experiment again once it is completed."
            )
        experiments = analysis.get("experiments") or []
        if status != "completed" or not experiments:
            raise ValueError(
                f"Seyval's analysis of commit {commit_hash[:12]} ended with "
                f"status {status!r} and {len(experiments)} experiment(s): "
                f"{analysis.get('error') or 'no runnable experiment found'}"
            )
        primary = (analysis.get("primary_ids") or [None])[0]
        experiment_id = primary or experiments[0]["id"]
        return str(analysis["analysis_id"]), str(experiment_id)

    def build_graph(self):
        graph_builder = StateGraph(
            DispatchExperimentSubgraphState,
            input_schema=DispatchExperimentSubgraphInputState,
            output_schema=DispatchExperimentSubgraphOutputState,
        )
        graph_builder.add_node("dispatch_experiment", self._dispatch)
        graph_builder.add_edge(START, "dispatch_experiment")
        graph_builder.add_edge("dispatch_experiment", END)
        return graph_builder.compile()
