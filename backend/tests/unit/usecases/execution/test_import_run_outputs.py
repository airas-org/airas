"""Guards around importing run outputs into the repository."""

import base64
import hashlib
import json
from typing import cast

import httpx
import pytest

from airas.core.types.github import GitHubConfig
from airas.core.types.run_stage import RunStage
from airas.infra.github_client import GithubClient
from airas.infra.run_output_store import SeyvalOutputStore
from airas.infra.seyval_client import SeyvalClient
from airas.usecases.execution.import_run_outputs import import_run_outputs
from airas.usecases.execution.nodes.collect_run_outputs import (
    MAX_TOTAL_BYTES,
    _is_importable,
    collect_run_outputs,
)

GITHUB_CONFIG = GitHubConfig(
    github_owner="airas-org",
    repository_name="experiment-repo",
    branch_name="main",
)
GIT_URL = "https://github.com/airas-org/experiment-repo"

FIGURE = ".research/results/run-1/figure.pdf"
METRICS = ".research/results/run-1/metrics.json"

SEYVAL_RUN_COMMIT = "a" * 40
SEYVAL_COMMAND_ARGS = ["python", "src/train.py", "mode=full", "+seed=7"]
SEYVAL_PARAMETERS = {"mode": "full", "seed": 7, "batch_size": 128}


class FakeSeyvalClient:
    def __init__(self, outputs: dict | None = None, runs: list | None = None):
        self._outputs = outputs or {}
        self._runs = runs or []
        self.downloaded: list[str] = []

    async def alist_repositories(self) -> list[dict]:
        return [{"id": "repo-uuid", "git_url": GIT_URL + ".git"}]

    async def alist_runs(self, repository_id: str) -> list:
        return self._runs

    async def aget_run_outputs(self, run_id: str) -> dict:
        return self._outputs

    async def adownload(self, url: str) -> bytes:
        self.downloaded.append(url)
        return f"content-of:{url}".encode()


def _store(client: FakeSeyvalClient) -> SeyvalOutputStore:
    return SeyvalOutputStore(cast(SeyvalClient, client), GIT_URL)


def _output(path: str, size_bytes: int = 10) -> dict:
    return {
        "path": path,
        "size_bytes": size_bytes,
        "last_modified": "2026-08-04T00:00:00Z",
        "download_url": f"https://s3.example/{path}?sig=abc",
    }


def _content(path: str) -> bytes:
    return f"content-of:https://s3.example/{path}?sig=abc".encode()


def _completed_run(run_id: str) -> dict:
    return {
        "run_id": run_id,
        "status": "completed",
        "commit_hash": SEYVAL_RUN_COMMIT,
        "command_args": SEYVAL_COMMAND_ARGS,
        "resolved_parameters": SEYVAL_PARAMETERS,
    }


# --------------------------------------------------
# Path filtering — output paths come from untrusted experiment code
# --------------------------------------------------


@pytest.mark.parametrize(
    "path",
    [
        METRICS,
        FIGURE,
        ".research/results/metrics.json",
        ".research/results/a/b/c/deep.png",
    ],
)
def test_importable_paths(path: str):
    assert _is_importable(path) is True


@pytest.mark.parametrize(
    "path",
    [
        "",
        "wandb/run-1/output.log",  # outside the results directory
        ".research/latex/main.tex",  # a different part of the repo
        ".research/results/../../etc/passwd",  # escapes via ..
        "/etc/passwd",  # absolute
        "/.research/results/x.png",
        "..",
        ".research/results/",  # normpath strips the trailing slash
        r".research\results\x.png",  # backslash separators
        # the import writes the declaration; a run must not supply its own
        ".research/results/.provenance.json",
    ],
)
def test_rejected_paths(path: str):
    assert _is_importable(path) is False


# --------------------------------------------------
# collect_run_outputs
# --------------------------------------------------


async def test_collect_downloads_only_results_files():
    client = FakeSeyvalClient(
        outputs={
            "outputs": [
                _output(METRICS),
                _output(FIGURE),
                _output("wandb/debug.log"),
                _output("checkpoints/model.pt"),
            ],
            "truncated": False,
        }
    )

    collected = await collect_run_outputs(_store(client), "run-uuid")

    assert set(collected) == {METRICS, FIGURE}
    assert len(client.downloaded) == 2
    assert collected[FIGURE] == _content(FIGURE)


async def test_collect_fails_when_listing_truncated():
    client = FakeSeyvalClient(
        outputs={"outputs": [_output(METRICS)], "truncated": True},
    )

    with pytest.raises(ValueError, match="truncated"):
        await collect_run_outputs(_store(client), "run-uuid")

    # Nothing is imported from a partial listing.
    assert client.downloaded == []


async def test_collect_fails_when_no_results_files():
    client = FakeSeyvalClient(
        outputs={"outputs": [_output("wandb/debug.log")], "truncated": False},
    )

    with pytest.raises(ValueError, match="no files under"):
        await collect_run_outputs(_store(client), "run-uuid")


async def test_collect_fails_when_download_url_missing():
    entry = _output(FIGURE)
    del entry["download_url"]
    client = FakeSeyvalClient(outputs={"outputs": [entry], "truncated": False})

    # Names the file rather than surfacing a bare KeyError from the gather.
    with pytest.raises(ValueError, match=r"figure\.pdf.*download_url"):
        await collect_run_outputs(_store(client), "run-uuid")


async def test_collect_fails_when_batch_too_large():
    client = FakeSeyvalClient(
        outputs={
            "outputs": [_output(FIGURE, size_bytes=MAX_TOTAL_BYTES + 1)],
            "truncated": False,
        }
    )

    with pytest.raises(ValueError, match="import limit"):
        await collect_run_outputs(_store(client), "run-uuid")


# --------------------------------------------------
# Whole subgraph
# --------------------------------------------------


def _github_client_capturing(blobs: list[dict]) -> GithubClient:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if request.method == "GET" and "/branches/" in path:
            return httpx.Response(
                200,
                json={
                    "commit": {"sha": "c" * 40, "commit": {"tree": {"sha": "t" * 40}}}
                },
            )
        if request.method == "GET" and "/contents/" in path:
            # No provenance manifest on the branch yet.
            return httpx.Response(404, json={"message": "Not Found"})
        if path.endswith("/git/blobs"):
            blobs.append(json.loads(request.content))
            return httpx.Response(201, json={"sha": f"blob{len(blobs)}"})
        if path.endswith("/git/trees"):
            return httpx.Response(201, json={"sha": "n" * 40})
        if path.endswith("/git/commits"):
            return httpx.Response(201, json={"sha": "d" * 40})
        if "/git/refs/" in path:
            return httpx.Response(200, json={})
        raise AssertionError(f"Unexpected request: {request.method} {path}")

    return GithubClient(
        github_token="test-token",
        async_session=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )


async def test_import_commits_downloaded_outputs_as_binary():
    seyval_client = FakeSeyvalClient(
        outputs={
            "outputs": [_output(METRICS), _output(FIGURE), _output("wandb/debug.log")],
            "truncated": False,
        },
        runs=[_completed_run("seyval-run-uuid")],
    )
    blobs: list[dict] = []

    result = await import_run_outputs(
        GITHUB_CONFIG,
        "run-1",
        store=_store(seyval_client),
        github_client=_github_client_capturing(blobs),
        execution_id="seyval-run-uuid",
        run_stage=RunStage.FULL,
    )

    assert result["imported"] is True
    assert result["execution_id"] == "seyval-run-uuid"
    assert result["imported_paths"] == sorted([METRICS, FIGURE])
    assert result["total_bytes"] > 0
    assert result["import_commit_sha"] == "d" * 40

    # Downloaded bytes reach GitHub base64-encoded, byte-for-byte; the
    # provenance manifest rides along as one extra text blob.
    binary_blobs = [b for b in blobs if b["encoding"] == "base64"]
    assert len(binary_blobs) == 2
    committed = {base64.b64decode(blob["content"]) for blob in binary_blobs}
    assert _content(FIGURE) in committed

    text_blobs = [b for b in blobs if b["encoding"] == "utf-8"]
    assert len(text_blobs) == 1
    manifest = json.loads(text_blobs[0]["content"])
    assert manifest["dirs"]["run-1"] == {
        "execution_id": "seyval-run-uuid",
        "backend": "seyval",
        "commit_hash": SEYVAL_RUN_COMMIT,
        # Lifted from the recorded argv, which the experiment code cannot
        # write — this is what makes a declared override checkable against
        # the parameters the run was actually dispatched with.
        "overrides": {"mode": "full", "seed": "7"},
        "parameters": {"mode": "full", "seed": "7", "batch_size": "128"},
        # What the gate falls back to once the backend drops the run.
        "files": {
            METRICS: hashlib.sha256(_content(METRICS)).hexdigest(),
            FIGURE: hashlib.sha256(_content(FIGURE)).hexdigest(),
        },
    }


async def test_import_succeeds_even_when_run_metadata_fetch_fails():
    """The commit hash in the manifest is reader convenience, not a gate."""
    seyval_client = FakeSeyvalClient(
        outputs={"outputs": [_output(METRICS)], "truncated": False},
    )

    async def broken_alist_runs(repository_id: str) -> list:
        raise RuntimeError("seyval metadata endpoint down")

    seyval_client.alist_runs = broken_alist_runs
    blobs: list[dict] = []

    result = await import_run_outputs(
        GITHUB_CONFIG,
        "run-1",
        store=_store(seyval_client),
        github_client=_github_client_capturing(blobs),
        execution_id="seyval-run-uuid",
        run_stage=RunStage.FULL,
    )

    assert result["imported"] is True
    manifest = json.loads(next(b for b in blobs if b["encoding"] == "utf-8")["content"])
    assert manifest["dirs"]["run-1"]["execution_id"] == "seyval-run-uuid"
    assert manifest["dirs"]["run-1"]["commit_hash"] is None
