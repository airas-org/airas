import hashlib
import io
import json
import re
import zipfile
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Literal

from airas.core.research_paths import (
    FETCH_LITERATURE_WORKFLOW_PATH,
    FULLTEXT_FILENAME,
    SOURCE_METADATA_FILENAME,
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
from airas.research_record.read.load_imported_source import imported_bibliography

# main にある source は入るときに照合済みなので、artifact の保持期限が過ぎても困らない
MAIN_REF = "origin/main"


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
        raise RunExpired(
            f"{name} has expired (GitHub keeps artifacts 90 days) — fetch it "
            "again with dispatch_literature_fetch"
        )

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


class NotALiteratureFetch(LookupError):
    """The run a source names cannot vouch for it; the message reads after "names"."""


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
        raise NotALiteratureFetch(f"run {workflow_run_id}, which does not exist")
    if run.get("path") != FETCH_LITERATURE_WORKFLOW_PATH:
        raise NotALiteratureFetch(
            f"run {workflow_run_id}, which is {run.get('path')}, "
            f"not {FETCH_LITERATURE_WORKFLOW_PATH}"
        )
    if run.get("conclusion") != "success":
        raise NotALiteratureFetch(
            f"fetch_literature.yml run {workflow_run_id}, which did not succeed "
            f"({run.get('conclusion')})"
        )
    return await download_literature_artifact(
        github_client, owner, repo, int(workflow_run_id)
    )


async def _problem(
    root: Path,
    source_id: str,
    imported: ImportedSource | None,
    artifact_of: Callable[[str], Awaitable[dict[str, dict[str, bytes]]]],
) -> str | None:
    relpath = f"{SOURCES_DIR}/{source_id}"
    if imported is None:
        return (
            f"{relpath} has no entry in {SOURCES_PROVENANCE_PATH}, so it was not "
            "added by fetch_literature.yml — only dispatch_literature_fetch may add "
            "sources"
        )

    run = f"fetch_literature.yml run {imported.workflow_run_id}"
    try:
        entries = await artifact_of(imported.workflow_run_id)
    except NotALiteratureFetch as e:
        return f"{relpath} names {e}"
    except RunExpired as e:
        return f"{relpath} cannot be checked: {e}"
    except Exception as e:
        return f"{relpath} cannot be checked against its artifact: {e}"
    if imported.entry not in entries:
        return f"{relpath}: {run}'s artifact has no entry {imported.entry}"

    on_disk = {
        p.name: p.read_bytes() for p in (root / relpath).iterdir() if p.is_file()
    }
    expected, actual = _sha256s(entries[imported.entry]), _sha256s(on_disk)
    if expected != actual:
        differing = sorted(
            n for n in {*expected, *actual} if expected.get(n) != actual.get(n)
        )
        verb = "differs" if len(differing) == 1 else "differ"
        return (
            f"{relpath}: {', '.join(differing)} {verb} from entry {imported.entry} "
            f"of {run}'s artifact — changed after the run downloaded it"
        )
    return None


def _bibliography_problem(root: Path, source: LiteratureSource) -> str | None:
    """None when the record's fields are what metadata.json says, as preregister wrote them."""
    metadata = json.loads(
        (root / SOURCES_DIR / source.id / SOURCE_METADATA_FILENAME).read_text(
            encoding="utf-8"
        )
    )
    differing = [
        field
        for field, value in imported_bibliography(metadata).items()
        if getattr(source, field) != value
    ]
    if not differing:
        return None
    verb = "differs" if len(differing) == 1 else "differ"
    return (
        f"literature[{source.id}]: {', '.join(differing)} {verb} from "
        f"{SOURCES_DIR}/{source.id}/{SOURCE_METADATA_FILENAME}, which "
        "preregister_record copies the record's fields from"
    )


async def verify_sources_came_from_artifacts(
    root: Path,
    record: ResearchRecord,
    verification: RecordVerification,
    github_client_factory: Callable[[], GithubClient],
) -> None:
    """Every .research/sources/<id>/ new to main, cited or not, is byte for byte
    its fetch_literature.yml run's artifact entry — whatever the record claims
    it is — and one on main never changes. Only code the record cites (git)
    is written by preregister instead. The record's fields for an imported
    source are its metadata.json's."""
    sources_dir = root / SOURCES_DIR
    directories = (
        sorted(p.name for p in sources_dir.iterdir() if re.fullmatch(r"s\d+", p.name))
        if sources_dir.is_dir()
        else []
    )
    cited = {s.id: s for s in record.latest_literature()}
    # preregister が書くのは論文を伴わないコードの snapshot だけ。本文や識別子があれば論文
    code = {
        i
        for i, s in cited.items()
        if s.verified_by == "git"
        and s.fulltext is None
        and not (s.doi or s.arxiv_id)
        and not (sources_dir / i / FULLTEXT_FILENAME).exists()
        and not (sources_dir / i / SOURCE_METADATA_FILENAME).exists()
    }

    def status(
        source_id: str, reason: str, verdict: Literal["verified", "mismatch"]
    ) -> None:
        verification.append_declaration_status(
            f"literature[{source_id}]"
            if source_id in cited
            else f"{SOURCES_DIR}/{source_id}",
            reason,
            verdict,
            evidence_path=f"{SOURCES_DIR}/{source_id}",
        )

    # is_file() と read_bytes() はリンクを辿るので、リンク先だけ書き換えれば git diff に出ない
    for directory in directories:
        source_dir = sources_dir / directory
        if source_dir.is_symlink() or any(p.is_symlink() for p in source_dir.iterdir()):
            status(
                directory,
                f"{SOURCES_DIR}/{directory} is or contains a symlink — sources "
                "must be regular files",
                "mismatch",
            )

    on_main = {
        d
        for d in directories
        if path_exists_at_commit(root, MAIN_REF, f"{SOURCES_DIR}/{d}")
    }
    for directory in sorted(on_main):
        if differs_from_commit(root, MAIN_REF, f"{SOURCES_DIR}/{directory}"):
            status(
                directory,
                f"{SOURCES_DIR}/{directory} differs from {MAIN_REF} — a source "
                "is never changed once merged",
                "mismatch",
            )

    # 記録上は取り込み済みでも、ディレクトリが無ければ照合する artifact も無い
    for source_id in cited:
        if source_id not in code and source_id not in directories:
            status(
                source_id,
                f"the record cites {source_id}, but {SOURCES_DIR}/{source_id} "
                "does not exist",
                "mismatch",
            )

    for source_id, source in cited.items():
        if (
            source_id in directories
            and (sources_dir / source_id / SOURCE_METADATA_FILENAME).is_file()
        ):
            if problem := _bibliography_problem(root, source):
                status(source_id, problem, "mismatch")

    new = [d for d in directories if d not in on_main and d not in code]
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
        for directory in new:
            status(
                directory,
                f"{SOURCES_DIR}/{directory} cannot be checked against its "
                f"artifact: {e}",
                "mismatch",
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

    for directory in new:
        problem = await _problem(
            root, directory, provenance.get(directory), artifact_of
        )
        status(
            directory,
            problem
            or f"{SOURCES_DIR}/{directory} is byte for byte entry "
            f"{provenance[directory].entry} of the artifact that fetch_literature.yml "
            f"run {provenance[directory].workflow_run_id} downloaded",
            "mismatch" if problem else "verified",
        )
