import hashlib
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
from airas.infra.run_output_store import RunOutputStore
from airas.usecases.executors.import_run_outputs_subgraph.nodes.collect_run_outputs import (
    collect_run_outputs,
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
    run_overrides: dict[str, str]
    run_parameters: dict[str, str]
    run_commit_hash: str | None


class ImportRunOutputsSubgraph:
    """Commit a run's stored outputs under RESULTS_DIR, with the provenance
    manifest the record gate pins its cross-check to, in one commit."""

    def __init__(
        self,
        store: RunOutputStore,
        github_client: GithubClient,
        execution_id: str,
        run_stage: RunStage | None = None,
    ):
        self.store = store
        self.github_client = github_client
        self.run_stage = run_stage or RunStage.FULL
        self.execution_id = execution_id

    @record_execution_time
    async def _collect_run_outputs(
        self, state: ImportRunOutputsSubgraphState
    ) -> dict[str, dict[str, bytes] | dict[str, str] | str | None]:
        execution_id = self.execution_id
        outputs = await collect_run_outputs(self.store, execution_id)

        # Best effort: verification re-fetches the run from the backend, so a
        # failed metadata fetch must not fail an import whose outputs downloaded.
        commit_hash: str | None = None
        overrides: dict[str, str] = {}
        parameters: dict[str, str] = {}
        try:
            runs = await self.store.alist_runs()
            run = next(r for r in runs if r.execution_id == execution_id)
            commit_hash = run.commit_hash
            overrides = run.overrides or {}
            parameters = run.parameters or {}
        except Exception as e:
            logger.warning(
                f"Could not fetch run metadata for {execution_id}; the "
                f"manifest will omit its commit hash and parameters: {e}"
            )
        return {
            "execution_id": execution_id,
            "outputs": outputs,
            "run_commit_hash": commit_hash,
            "run_overrides": overrides,
            "run_parameters": parameters,
        }

    async def _load_manifest(
        self, github_config: GitHubConfig
    ) -> RunProvenanceManifest:
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

        manifest = await self._load_manifest(github_config)
        prefix = f"{RESULTS_DIR}/"
        by_dir: dict[str, dict[str, str]] = {}
        for path, content in outputs.items():
            relative = path.removeprefix(prefix)
            if "/" not in relative:
                continue  # a file directly under RESULTS_DIR has no directory
            dir_name = relative.split("/", 1)[0]
            by_dir.setdefault(dir_name, {})[path] = hashlib.sha256(content).hexdigest()
        for dir_name, files in by_dir.items():
            manifest.dirs[dir_name] = ResultsDirProvenance(
                execution_id=execution_id,
                backend=self.store.backend,
                commit_hash=state.get("run_commit_hash"),
                overrides=state.get("run_overrides") or {},
                parameters=state.get("run_parameters") or {},
                files=files,
            )

        files_to_commit: dict[str, str | bytes] = dict(outputs)
        files_to_commit[PROVENANCE_MANIFEST_PATH] = (
            manifest.model_dump_json(indent=2) + "\n"
        )
        import_commit_sha = await self.github_client.acommit_multiple_files(
            github_owner=github_config.github_owner,
            repository_name=github_config.repository_name,
            branch_name=github_config.branch_name,
            files=files_to_commit,
            commit_message=(
                f"Import {self.store.backend} run outputs for {state['run_id']} "
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

        graph_builder.add_node("collect_run_outputs", self._collect_run_outputs)
        graph_builder.add_node("commit_outputs", self._commit_outputs)

        graph_builder.add_edge(START, "collect_run_outputs")
        graph_builder.add_edge("collect_run_outputs", "commit_outputs")
        graph_builder.add_edge("commit_outputs", END)

        return graph_builder.compile()
