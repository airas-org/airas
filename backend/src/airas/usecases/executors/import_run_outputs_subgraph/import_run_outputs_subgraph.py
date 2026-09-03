import logging

from langgraph.graph import END, START, StateGraph
from pydantic import ValidationError
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.logging_utils import setup_logging
from airas.core.research_paths import RESULTS_DIR
from airas.core.types.experiment_history import RunStage
from airas.core.types.github import GitHubConfig
from airas.core.types.run_provenance import (
    PROVENANCE_MANIFEST_PATH,
    ResultsDirProvenance,
    RunProvenanceManifest,
)
from airas.infra.github_client import GithubClient, GithubClientFatalError
from airas.infra.seyval_client import SeyvalClient
from airas.usecases.executors.import_run_outputs_subgraph.nodes.collect_run_outputs import (
    collect_run_outputs,
)
from airas.usecases.executors.import_run_outputs_subgraph.nodes.resolve_execution_id import (
    resolve_execution_id,
)
from airas.usecases.verification.run_parameters import (
    parse_overrides,
    parse_parameters,
)

setup_logging()
logger = logging.getLogger(__name__)


def record_execution_time(f):
    return time_node("import_run_outputs_subgraph")(f)  # noqa: E731


class ImportRunOutputsSubgraphInputState(TypedDict):
    github_config: GitHubConfig
    run_id: str


class ImportRunOutputsSubgraphOutputState(ExecutionTimeState):
    imported: bool
    execution_id: str
    imported_paths: list[str]
    total_bytes: int
    import_commit_sha: str


class ImportRunOutputsSubgraphState(
    ImportRunOutputsSubgraphInputState,
    ImportRunOutputsSubgraphOutputState,
    total=False,
):
    outputs: dict[str, bytes]
    seyval_overrides: dict[str, str]
    seyval_parameters: dict[str, str]
    seyval_commit_hash: str | None


class ImportRunOutputsSubgraph:
    """Copy a Seyval run's result files into the experiment repository.

    Seyval pulls the repository to run it but never pushes back: outputs are
    captured from the run's working directory into Seyval's own storage. This
    subgraph closes that loop by downloading the files under the results
    directory and committing them at the same paths, which is where
    `fetch_experiment_results` and the LaTeX build already look. The same
    commit carries the provenance manifest declaring which run produced
    each directory, which is what the paper-value verification pins its
    Seyval cross-check to.

    The bytes never leave this process — see `collect_run_outputs` for why
    that matters.
    """

    def __init__(
        self,
        seyval_client: SeyvalClient,
        github_client: GithubClient,
        run_stage: RunStage | None = None,
        execution_id: str | None = None,
    ):
        self.seyval_client = seyval_client
        self.github_client = github_client
        self.run_stage = run_stage or RunStage.FULL
        self.execution_id = execution_id

    @record_execution_time
    async def _resolve_execution_id(
        self, state: ImportRunOutputsSubgraphState
    ) -> dict[str, str]:
        if self.execution_id:
            return {"execution_id": self.execution_id}

        execution_id = await resolve_execution_id(
            self.seyval_client,
            state["github_config"],
            state["run_id"],
            self.run_stage.value,
        )
        return {"execution_id": execution_id}

    @record_execution_time
    async def _collect_run_outputs(
        self, state: ImportRunOutputsSubgraphState
    ) -> dict[str, dict[str, bytes] | dict[str, str] | str | None]:
        execution_id = state["execution_id"]
        outputs = await collect_run_outputs(self.seyval_client, execution_id)

        # The commit the run executed, for the provenance declaration. Its
        # authoritative copy lives in Seyval and verification re-fetches it
        # from there, so this is best-effort reader convenience — a failed
        # metadata fetch must not fail an import whose outputs downloaded.
        commit_hash: str | None = None
        overrides: dict[str, str] = {}
        parameters: dict[str, str] = {}
        try:
            run = await self.seyval_client.aget_run(execution_id)
            commit_hash = run.get("commit_hash")
            overrides = parse_overrides(run.get("command_args"))
            parameters = parse_parameters(run)
        except Exception as e:
            logger.warning(
                f"Could not fetch run metadata for {execution_id}; the "
                f"manifest will omit its commit hash and parameters: {e}"
            )
        return {
            "outputs": outputs,
            "seyval_commit_hash": commit_hash,
            "seyval_overrides": overrides,
            "seyval_parameters": parameters,
        }

    async def _load_manifest(
        self, github_config: GitHubConfig
    ) -> RunProvenanceManifest:
        """The provenance manifest currently on the branch, or a fresh one."""
        try:
            raw = await self.github_client.aget_repository_content(
                github_owner=github_config.github_owner,
                repository_name=github_config.repository_name,
                file_path=PROVENANCE_MANIFEST_PATH,
                branch_name=github_config.branch_name,
                as_="bytes",
            )
        except GithubClientFatalError as e:
            if e.status_code == 404:
                return RunProvenanceManifest()
            raise
        try:
            assert isinstance(raw, bytes)
            return RunProvenanceManifest.model_validate_json(raw)
        except (ValidationError, ValueError):
            logger.warning(
                f"Existing {PROVENANCE_MANIFEST_PATH} is unreadable; rebuilding "
                "it for the directories this import covers"
            )
            return RunProvenanceManifest()

    @record_execution_time
    async def _commit_outputs(
        self, state: ImportRunOutputsSubgraphState
    ) -> dict[str, bool | list[str] | int | str]:
        outputs = state["outputs"]
        github_config = state["github_config"]
        execution_id = state["execution_id"]

        # Declare, in the same commit as the data, which run produced each
        # results directory. Verification pins its byte-comparison to the
        # declared run, so with several completed runs of one experiment
        # only this one backs the paper.
        manifest = await self._load_manifest(github_config)
        prefix = f"{RESULTS_DIR}/"
        for path in outputs:
            relative = path.removeprefix(prefix)
            if "/" not in relative:
                continue  # a file directly under RESULTS_DIR has no directory
            dir_name = relative.split("/", 1)[0]
            manifest.dirs[dir_name] = ResultsDirProvenance(
                execution_id=execution_id,
                commit_hash=state.get("seyval_commit_hash"),
                overrides=state.get("seyval_overrides") or {},
                parameters=state.get("seyval_parameters") or {},
            )

        # One commit for the whole batch, so the repository is never left
        # holding half a run's results.
        files: dict[str, str | bytes] = dict(outputs)
        files[PROVENANCE_MANIFEST_PATH] = manifest.model_dump_json(indent=2) + "\n"
        import_commit_sha = await self.github_client.acommit_multiple_files(
            github_owner=github_config.github_owner,
            repository_name=github_config.repository_name,
            branch_name=github_config.branch_name,
            files=files,
            commit_message=(
                f"Import Seyval run outputs for {state['run_id']} "
                f"({self.run_stage.value}) from run {execution_id}"
            ),
        )

        paths = sorted(outputs)
        total_bytes = sum(len(content) for content in outputs.values())
        logger.info(
            f"Imported {len(paths)} files ({total_bytes} bytes) into "
            f"{RESULTS_DIR}/ on branch '{github_config.branch_name}' "
            f"as commit {import_commit_sha[:12]}"
        )
        return {
            "imported": bool(import_commit_sha),
            "imported_paths": paths,
            "total_bytes": total_bytes,
            "import_commit_sha": import_commit_sha,
        }

    def build_graph(self):
        graph_builder = StateGraph(
            ImportRunOutputsSubgraphState,
            input_schema=ImportRunOutputsSubgraphInputState,
            output_schema=ImportRunOutputsSubgraphOutputState,
        )

        graph_builder.add_node("resolve_execution_id", self._resolve_execution_id)
        graph_builder.add_node("collect_run_outputs", self._collect_run_outputs)
        graph_builder.add_node("commit_outputs", self._commit_outputs)

        graph_builder.add_edge(START, "resolve_execution_id")
        graph_builder.add_edge("resolve_execution_id", "collect_run_outputs")
        graph_builder.add_edge("collect_run_outputs", "commit_outputs")
        graph_builder.add_edge("commit_outputs", END)

        return graph_builder.compile()
