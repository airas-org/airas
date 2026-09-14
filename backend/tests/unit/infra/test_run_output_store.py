import io
import zipfile
from typing import Any, cast

import pytest

from airas.infra import run_output_store
from airas.infra.github_client import GithubClient
from airas.infra.run_output_store import (
    MAX_TOTAL_BYTES,
    GithubActionsOutputStore,
    RunExpired,
)

RUN_DIR = ".research/results/run-1"


class FakeGithubClient:
    def __init__(
        self,
        runs: list[dict[str, Any]],
        artifacts: list[dict[str, Any]],
        zip_bytes: bytes,
    ) -> None:
        self.runs = runs
        self.artifacts = artifacts
        self.zip_bytes = zip_bytes
        self.downloads = 0

    async def alist_workflow_runs(self, owner: str, repo: str, **kw: Any) -> dict:
        page = int(kw.get("page", 1))
        return {"workflow_runs": self.runs[(page - 1) * 100 : page * 100]}

    async def alist_workflow_run_artifacts(
        self, owner: str, repo: str, workflow_run_id: int
    ) -> dict:
        return {"artifacts": self.artifacts}

    async def adownload_artifact_archive(
        self, owner: str, repo: str, artifact_id: int
    ) -> bytes:
        self.downloads += 1
        return self.zip_bytes


def _zip(files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zipped:
        for name, content in files.items():
            zipped.writestr(name, content)
    return buffer.getvalue()


def _store(client: FakeGithubClient) -> GithubActionsOutputStore:
    return GithubActionsOutputStore(cast(GithubClient, client), "org", "repo")


def _artifact(expired: bool = False) -> dict[str, Any]:
    return {"id": 7, "name": "full-12345-run-1", "expired": expired}


async def test_artifact_members_map_under_the_run_directory() -> None:
    client = FakeGithubClient(
        runs=[],
        artifacts=[_artifact()],
        zip_bytes=_zip({"metrics.json": b"{}", "eval_inputs/task.json": b"[]"}),
    )
    store = _store(client)

    outputs = await store.alist_outputs("12345")
    assert outputs == {
        f"{RUN_DIR}/metrics.json": 2,
        f"{RUN_DIR}/eval_inputs/task.json": 2,
    }
    assert await store.adownload("12345", f"{RUN_DIR}/eval_inputs/task.json") == b"[]"
    assert client.downloads == 1  # one archive per run, cached


async def test_an_expired_artifact_raises_run_expired() -> None:
    client = FakeGithubClient(
        runs=[], artifacts=[_artifact(expired=True)], zip_bytes=b""
    )
    with pytest.raises(RunExpired):
        await _store(client).alist_outputs("12345")


async def test_a_run_without_a_results_artifact_is_unknown() -> None:
    client = FakeGithubClient(
        runs=[], artifacts=[{"id": 1, "name": "logs"}], zip_bytes=b""
    )
    with pytest.raises(LookupError):
        await _store(client).alist_outputs("12345")


async def test_runs_carry_the_mode_from_the_run_name() -> None:
    client = FakeGithubClient(
        runs=[
            {
                "id": 12345,
                "status": "completed",
                "conclusion": "success",
                "head_sha": "a" * 40,
                "display_title": "[full] run-1",
            },
            {
                "id": 12346,
                "status": "completed",
                "conclusion": "failure",
                "head_sha": "a" * 40,
            },
        ],
        artifacts=[],
        zip_bytes=b"",
    )
    ok, failed = await _store(client).alist_runs()
    assert ok.execution_id == "12345"
    assert ok.status == "completed"
    assert ok.commit_hash == "a" * 40
    assert ok.overrides == {"mode": "full"}
    assert failed.status == "failure"
    assert failed.overrides is None


async def test_an_artifact_over_the_import_cap_is_refused_before_download() -> None:
    artifact = {**_artifact(), "size_in_bytes": MAX_TOTAL_BYTES + 1}
    client = FakeGithubClient(runs=[], artifacts=[artifact], zip_bytes=b"")
    with pytest.raises(ValueError, match="import limit"):
        await _store(client).alist_outputs("12345")
    assert client.downloads == 0


async def test_an_archive_that_inflates_over_the_cap_is_refused_unread(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(run_output_store, "MAX_TOTAL_BYTES", 8)
    client = FakeGithubClient(
        runs=[], artifacts=[_artifact()], zip_bytes=_zip({"metrics.json": b"0" * 64})
    )
    with pytest.raises(ValueError, match="inflates"):
        await _store(client).alist_outputs("12345")


async def test_runs_are_paged_past_the_first_hundred() -> None:
    runs = [
        {"id": i, "status": "completed", "conclusion": "success", "head_sha": "a" * 40}
        for i in range(101)
    ]
    client = FakeGithubClient(runs=runs, artifacts=[], zip_bytes=b"")
    listed = await _store(client).alist_runs()
    assert [r.execution_id for r in listed][-1] == "100"
    assert len(listed) == 101
