import hashlib
import io
import zipfile
from collections.abc import Awaitable, Callable
from pathlib import Path

from airas.core.research_paths import (
    FETCH_LITERATURE_WORKFLOW_PATH,
    SOURCES_DIR,
    SOURCES_PROVENANCE_PATH,
)
from airas.core.types.imported_source import SOURCES_PROVENANCE, ImportedSource
from airas.core.types.record_verification import RecordVerification
from airas.core.types.research_record import LiteratureSource, ResearchRecord
from airas.infra.github_client import GithubClient
from airas.infra.local_git import (
    differs_from_commit,
    path_exists_at_commit,
    remote_origin_url,
)
from airas.infra.run_output_store import RunExpired, github_owner_and_repository

# main にある source は入るときに照合済みなので、artifact の保持期限が過ぎても困らない
MAIN_REF = "origin/main"

# The verified_by of a source fetch_literature.yml imported: its search source.
IMPORTED_SOURCE_KINDS = frozenset(
    {"arxiv", "openalex", "semantic_scholar", "airas_db", "airas_records"}
)


async def download_literature_artifact(
    github_client: GithubClient,
    github_owner: str,
    repository_name: str,
    workflow_run_id: int,
) -> dict[str, dict[str, bytes]]:
    """Entry directory ("0", "1", …) -> file name -> bytes."""
    name = f"literature-{workflow_run_id}"
    response = await github_client.alist_workflow_run_artifacts(
        github_owner, repository_name, workflow_run_id
    )
    artifact = next(
        (a for a in (response or {}).get("artifacts", []) if a.get("name") == name),
        None,
    )
    if artifact is None:
        raise LookupError(f"workflow run {workflow_run_id} has no {name} artifact")

    if artifact.get("expired"):
        raise RunExpired(f"{name} has expired (GitHub's artifact retention)")

    zip_bytes = await github_client.adownload_artifact_archive(
        github_owner, repository_name, int(artifact["id"])
    )
    if not zip_bytes:
        raise LookupError(f"{name} is empty")

    entries: dict[str, dict[str, bytes]] = {}
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zipped:
        for info in zipped.infolist():
            if info.is_dir() or "/" not in info.filename:
                continue
            entry, file_name = info.filename.split("/", 1)
            entries.setdefault(entry, {})[file_name] = zipped.read(info)
    return entries


def _sha256s(files: dict[str, bytes]) -> dict[str, str]:
    return {
        name: hashlib.sha256(content).hexdigest() for name, content in files.items()
    }


async def _artifact_entries(
    github_client: GithubClient, owner: str, repo: str, workflow_run_id: str
) -> dict[str, dict[str, bytes]]:
    """The run's artifact, once the run is shown to be a successful
    fetch_literature.yml run: an artifact of any other workflow proves nothing."""
    run = await github_client.aget_workflow_run(owner, repo, int(workflow_run_id))
    if run is None:
        raise LookupError(f"workflow run {workflow_run_id} does not exist")
    if run.get("path") != FETCH_LITERATURE_WORKFLOW_PATH:
        raise LookupError(
            f"workflow run {workflow_run_id} is {run.get('path')}, "
            f"not {FETCH_LITERATURE_WORKFLOW_PATH}"
        )
    if run.get("conclusion") != "success":
        raise LookupError(
            f"workflow run {workflow_run_id} did not succeed ({run.get('conclusion')})"
        )
    return await download_literature_artifact(
        github_client, owner, repo, int(workflow_run_id)
    )


async def _problem(
    root: Path,
    source: LiteratureSource,
    imported: ImportedSource | None,
    artifact_of: Callable[[str], Awaitable[dict[str, dict[str, bytes]]]],
) -> str | None:
    relpath = f"{SOURCES_DIR}/{source.id}"
    if imported is None:
        return f"{relpath} is not in {SOURCES_PROVENANCE_PATH} (fetch_literature.yml writes it)"

    try:
        entries = await artifact_of(imported.workflow_run_id)
    except Exception as e:
        return f"{relpath} cannot be compared with its artifact: {e}"
    if imported.entry not in entries:
        return (
            f"{relpath}: run {imported.workflow_run_id}'s artifact has no "
            f"entry {imported.entry}"
        )

    on_disk = {
        p.name: p.read_bytes() for p in (root / relpath).iterdir() if p.is_file()
    }
    expected, actual = _sha256s(entries[imported.entry]), _sha256s(on_disk)
    if expected != actual:
        differing = sorted(
            n for n in {*expected, *actual} if expected.get(n) != actual.get(n)
        )
        return (
            f"{relpath}: {', '.join(differing)} differ from run "
            f"{imported.workflow_run_id}'s artifact entry {imported.entry}"
        )
    return None


async def verify_sources_came_from_artifacts(
    root: Path,
    record: ResearchRecord,
    verification: RecordVerification,
    github_client_factory: Callable[[], GithubClient],
) -> None:
    """Every source the record cites that fetch_literature.yml imported is, if new
    to main, byte for byte its run's artifact entry; once on main, never changed."""
    sources = [
        s for s in record.latest_literature() if s.verified_by in IMPORTED_SOURCE_KINDS
    ]
    new: list[LiteratureSource] = []
    for source in sources:
        relpath = f"{SOURCES_DIR}/{source.id}"
        if not path_exists_at_commit(root, MAIN_REF, relpath):
            new.append(source)
        elif differs_from_commit(root, MAIN_REF, relpath):
            verification.append_declaration_status(
                f"literature[{source.id}]",
                f"{relpath} differs from {MAIN_REF}: a source is never changed once on main",
                "mismatch",
                evidence_path=relpath,
            )
    if not new:
        return

    provenance_path = root / SOURCES_PROVENANCE_PATH
    provenance = (
        SOURCES_PROVENANCE.validate_json(provenance_path.read_bytes())
        if provenance_path.is_file()
        else {}
    )
    try:
        github_client = github_client_factory()
        owner, repo = github_owner_and_repository(remote_origin_url(root) or "")
    except Exception as e:
        for source in new:
            verification.append_declaration_status(
                f"literature[{source.id}]",
                f"{SOURCES_DIR}/{source.id} cannot be compared with its artifact: {e}",
                "mismatch",
                evidence_path=f"{SOURCES_DIR}/{source.id}",
            )
        return

    fetched: dict[str, dict[str, dict[str, bytes]] | Exception] = {}

    async def artifact_of(workflow_run_id: str) -> dict[str, dict[str, bytes]]:
        if workflow_run_id not in fetched:
            try:
                fetched[workflow_run_id] = await _artifact_entries(
                    github_client, owner, repo, workflow_run_id
                )
            except Exception as e:
                fetched[workflow_run_id] = e
        result = fetched[workflow_run_id]
        if isinstance(result, Exception):
            raise result
        return result

    for source in new:
        relpath = f"{SOURCES_DIR}/{source.id}"
        problem = await _problem(root, source, provenance.get(source.id), artifact_of)
        verification.append_declaration_status(
            f"literature[{source.id}]",
            problem
            or f"{relpath} is run {provenance[source.id].workflow_run_id}'s "
            "fetch_literature.yml artifact, byte for byte",
            "mismatch" if problem else "verified",
            evidence_path=relpath,
        )
