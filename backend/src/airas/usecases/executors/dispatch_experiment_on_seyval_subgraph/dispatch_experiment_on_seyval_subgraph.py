import logging
import re

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.logging_utils import setup_logging
from airas.core.research_paths import RESULTS_DIR
from airas.core.types.experiment_history import RunStage
from airas.core.types.github import GitHubConfig
from airas.infra.seyval_client import SeyvalClient

setup_logging()
logger = logging.getLogger(__name__)

# The CLI contract defined by airas-template's AGENTS.md. Seyval captures the
# run's whole working directory, so outputs come back under RESULTS_DIR too
# and can be copied into the repository as-is.
ENTRY_POINT_TEMPLATE = (
    "uv run python -u -m src.main run={run_id} "
    f"results_dir={RESULTS_DIR} " + "mode={mode}"
)


def seyval_experiment_id(run_id: str, mode: str) -> str:
    """Build the Seyval `experiment_id` for one run of an experiment.

    Importing a run's outputs looks the run up by this value, so dispatch
    and import must derive it identically — keep it defined here only.
    Note it is not unique per run: re-dispatching the same run_id and mode
    produces the same id.
    """
    return re.sub(r"[^a-z0-9_]", "_", f"{run_id}_{mode}".lower())


def record_execution_time(f):
    return time_node("dispatch_experiment_on_seyval_subgraph")(f)  # noqa: E731


class DispatchExperimentOnSeyvalSubgraphInputState(TypedDict):
    github_config: GitHubConfig
    run_id: str


class DispatchExperimentOnSeyvalSubgraphOutputState(ExecutionTimeState):
    dispatched: bool
    seyval_run_id: str
    seyval_run_url: str


class DispatchExperimentOnSeyvalSubgraphState(
    DispatchExperimentOnSeyvalSubgraphInputState,
    DispatchExperimentOnSeyvalSubgraphOutputState,
    total=False,
):
    pass


class DispatchExperimentOnSeyvalSubgraph:
    """Execute one experiment run on the Seyval compute platform.

    Seyval pulls the experiment repository from GitHub, so the run branch must
    be pushed before dispatching. The subgraph registers the repository
    (idempotent), refreshes it to resolve the branch head commit, ensures an
    analysis record exists for that commit, and starts a run whose entry
    command follows the airas-template CLI contract.
    """

    def __init__(
        self,
        seyval_client: SeyvalClient,
        compute_id: str | None = None,
        run_stage: RunStage | None = None,
        compute_type: str = "gpu-a10",
        required_env_vars: list[str] | None = None,
        inputs_from_runs: list[str] | None = None,
        time_limit: str | None = None,
        resource_count: int | None = None,
    ):
        self.seyval_client = seyval_client
        self.run_stage = run_stage or RunStage.SANITY
        # compute_id ("byo:<uuid>") picks a registered cluster; without one
        # Seyval falls back to its own managed compute. compute_type applies
        # either way — a registered cluster resolves it to the resources the
        # job asks for.
        self.compute_type = compute_type
        self.compute_id = compute_id
        # Earlier runs whose outputs this run reads (e.g. a measurement run
        # feeding a visualization run), and per-run resource requests a
        # registered cluster honours.
        self.inputs_from_runs = inputs_from_runs
        self.time_limit = time_limit
        self.resource_count = resource_count
        # W&B logging is part of the experiment-code contract, so runs need
        # the key registered on the Seyval side by default.
        self.required_env_vars = (
            required_env_vars if required_env_vars is not None else ["WANDB_API_KEY"]
        )

    async def _resolve_analysis_id(
        self, repository_id: str, commit_hash: str, branch: str
    ) -> str | None:
        """Find the analysis just created for `commit_hash`.

        Starting an analysis returns no record id, so the id has to be looked
        up separately. The listing is newest-first, so the first entry for the
        commit is the one we created. Returning None is safe: Seyval then binds
        the run to the newest analysis for that commit itself.
        """
        analyses = await self.seyval_client.alist_analyses(repository_id, branch=branch)
        for analysis in analyses:
            if analysis.get("commit_hash") == commit_hash:
                return analysis.get("analysis_id")

        logger.warning(
            f"No analysis found for commit {commit_hash[:12]} on branch "
            f"'{branch}'; letting Seyval pick the latest one for the commit."
        )
        return None

    @record_execution_time
    async def _dispatch_experiment_on_seyval(
        self, state: DispatchExperimentOnSeyvalSubgraphState
    ) -> dict[str, bool | str]:
        github_config = state["github_config"]
        run_id = state["run_id"]
        git_url = (
            f"https://github.com/{github_config.github_owner}/"
            f"{github_config.repository_name}"
        )

        repository = await self.seyval_client.aregister_repository(git_url)
        repository_id = repository["id"]

        pulled = await self.seyval_client.apull_repository(repository_id)
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

        await self.seyval_client.astart_analysis(
            repository_id, commit_hash, branch=github_config.branch_name
        )
        analysis_id = await self._resolve_analysis_id(
            repository_id, commit_hash, github_config.branch_name
        )

        mode = self.run_stage.value
        analyzed_experiment = {
            "id": seyval_experiment_id(run_id, mode),
            "title": f"{run_id} ({mode})",
            "description": (
                f"AIRAS experiment run '{run_id}' in {mode} mode, following the "
                "airas-template CLI contract."
            ),
            "entry_point": ENTRY_POINT_TEMPLATE.format(run_id=run_id, mode=mode),
            "language": "Python",
            "inputs": "config/run/*.yaml (Hydra run configs)",
            "outputs": f"{RESULTS_DIR} and W&B metrics",
            "required_env_vars": self.required_env_vars,
        }

        logger.info(
            f"Starting Seyval run for run_id={run_id} (mode={mode}, "
            f"compute_id={self.compute_id}, compute_type={self.compute_type}) "
            f"at commit {commit_hash[:12]}"
        )
        run = await self.seyval_client.astart_run(
            repository_id,
            commit_hash,
            analyzed_experiment,
            compute_type=self.compute_type,
            compute_id=self.compute_id,
            analysis_id=analysis_id,
            inputs_from_runs=self.inputs_from_runs,
            time_limit=self.time_limit,
            resource_count=self.resource_count,
        )

        return {
            "dispatched": True,
            "seyval_run_id": str(run["run_id"]),
            "seyval_run_url": run.get("run_url") or "",
        }

    def build_graph(self):
        graph_builder = StateGraph(
            DispatchExperimentOnSeyvalSubgraphState,
            input_schema=DispatchExperimentOnSeyvalSubgraphInputState,
            output_schema=DispatchExperimentOnSeyvalSubgraphOutputState,
        )

        graph_builder.add_node(
            "dispatch_experiment_on_seyval",
            self._dispatch_experiment_on_seyval,
        )

        graph_builder.add_edge(START, "dispatch_experiment_on_seyval")
        graph_builder.add_edge("dispatch_experiment_on_seyval", END)

        return graph_builder.compile()
