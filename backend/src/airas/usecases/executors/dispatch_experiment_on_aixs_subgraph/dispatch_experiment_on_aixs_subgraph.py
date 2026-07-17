import logging
import re

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.logging_utils import setup_logging
from airas.core.types.experiment_history import RunStage
from airas.core.types.github import GitHubConfig
from airas.infra.aixs_client import AixsClient

setup_logging()
logger = logging.getLogger(__name__)

# The CLI contract defined by airas-template's AGENTS.md.
_ENTRY_POINT_TEMPLATE = "uv run python -u -m src.main run={run_id} results_dir=.research/results mode={mode}"


def record_execution_time(f):
    return time_node("dispatch_experiment_on_aixs_subgraph")(f)  # noqa: E731


class DispatchExperimentOnAixsSubgraphInputState(TypedDict):
    github_config: GitHubConfig
    run_id: str


class DispatchExperimentOnAixsSubgraphOutputState(ExecutionTimeState):
    dispatched: bool
    aixs_run_id: str
    aixs_run_url: str


class DispatchExperimentOnAixsSubgraphState(
    DispatchExperimentOnAixsSubgraphInputState,
    DispatchExperimentOnAixsSubgraphOutputState,
    total=False,
):
    pass


class DispatchExperimentOnAixsSubgraph:
    """Execute one experiment run on the AIXS compute platform.

    AIXS pulls the experiment repository from GitHub, so the run branch must
    be pushed before dispatching. The subgraph registers the repository
    (idempotent), refreshes it to resolve the branch head commit, ensures an
    analysis record exists for that commit, and starts a run whose entry
    command follows the airas-template CLI contract.
    """

    def __init__(
        self,
        aixs_client: AixsClient,
        run_stage: RunStage | None = None,
        compute_type: str = "gpu-a10",
        compute_id: str | None = None,
        required_env_vars: list[str] | None = None,
    ):
        self.aixs_client = aixs_client
        self.run_stage = run_stage or RunStage.SANITY
        self.compute_type = compute_type
        self.compute_id = compute_id
        # W&B logging is part of the experiment-code contract, so runs need
        # the key registered on the AIXS side by default.
        self.required_env_vars = (
            required_env_vars if required_env_vars is not None else ["WANDB_API_KEY"]
        )

    @record_execution_time
    async def _dispatch_experiment_on_aixs(
        self, state: DispatchExperimentOnAixsSubgraphState
    ) -> dict[str, bool | str]:
        github_config = state["github_config"]
        run_id = state["run_id"]
        git_url = (
            f"https://github.com/{github_config.github_owner}/"
            f"{github_config.repository_name}"
        )

        repository = await self.aixs_client.aregister_repository(git_url)
        repository_id = repository["id"]

        pulled = await self.aixs_client.apull_repository(repository_id)
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

        analysis = await self.aixs_client.astart_analysis(
            repository_id, commit_hash, branch=github_config.branch_name
        )

        mode = self.run_stage.value
        analyzed_experiment = {
            "id": re.sub(r"[^a-z0-9_]", "_", f"{run_id}_{mode}".lower()),
            "title": f"{run_id} ({mode})",
            "description": (
                f"AIRAS experiment run '{run_id}' in {mode} mode, following the "
                "airas-template CLI contract."
            ),
            "entry_point": _ENTRY_POINT_TEMPLATE.format(run_id=run_id, mode=mode),
            "language": "Python",
            "inputs": "config/run/*.yaml (Hydra run configs)",
            "outputs": ".research/results and W&B metrics",
            "required_env_vars": self.required_env_vars,
        }

        logger.info(
            f"Starting AIXS run for run_id={run_id} (mode={mode}, "
            f"compute_type={self.compute_type}) at commit {commit_hash[:12]}"
        )
        run = await self.aixs_client.astart_run(
            repository_id,
            commit_hash,
            analyzed_experiment,
            compute_type=self.compute_type,
            compute_id=self.compute_id,
            analysis_id=analysis.get("id"),
        )

        return {
            "dispatched": True,
            "aixs_run_id": str(run["run_id"]),
            "aixs_run_url": run.get("run_url") or "",
        }

    def build_graph(self):
        graph_builder = StateGraph(
            DispatchExperimentOnAixsSubgraphState,
            input_schema=DispatchExperimentOnAixsSubgraphInputState,
            output_schema=DispatchExperimentOnAixsSubgraphOutputState,
        )

        graph_builder.add_node(
            "dispatch_experiment_on_aixs",
            self._dispatch_experiment_on_aixs,
        )

        graph_builder.add_edge(START, "dispatch_experiment_on_aixs")
        graph_builder.add_edge("dispatch_experiment_on_aixs", END)

        return graph_builder.compile()
