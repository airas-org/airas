"""Guards around importing Seyval run outputs into the repository."""

import base64
import json

import httpx
import pytest

from airas.core.types.experiment_history import RunStage
from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient
from airas.usecases.executors.import_run_outputs_subgraph.import_run_outputs_subgraph import (
    ImportRunOutputsSubgraph,
)
from airas.usecases.executors.import_run_outputs_subgraph.nodes.collect_run_outputs import (
    MAX_TOTAL_BYTES,
    _is_importable,
    collect_run_outputs,
)
from airas.usecases.executors.import_run_outputs_subgraph.nodes.resolve_execution_id import (
    resolve_execution_id,
)

GITHUB_CONFIG = GitHubConfig(
    github_owner="airas-org",
    repository_name="experiment-repo",
    branch_name="main",
)

FIGURE = ".research/results/run-1/figure.pdf"
METRICS = ".research/results/run-1/metrics.json"


SEYVAL_RUN_COMMIT = "a" * 40


class FakeSeyvalClient:
    """Stands in for SeyvalClient; records what was downloaded."""

    def __init__(self, outputs: dict | None = None, runs: list | None = None):
        self._outputs = outputs or {}
        self._runs = runs or []
        self.downloaded: list[str] = []

    async def aget_run_outputs(self, run_id: str) -> dict:
        return self._outputs

    async def adownload(self, url: str) -> bytes:
        self.downloaded.append(url)
        return f"content-of:{url}".encode()

    async def aregister_repository(self, git_url: str) -> dict:
        return {"id": "repo-uuid"}

    async def alist_runs(self, repository_id: str) -> list:
        return self._runs

    async def aget_run(self, run_id: str) -> dict:
        return {
            "run_id": run_id,
            "status": "completed",
            "commit_hash": SEYVAL_RUN_COMMIT,
        }


def _output(path: str, size_bytes: int = 10) -> dict:
    return {
        "path": path,
        "size_bytes": size_bytes,
        "last_modified": "2026-08-04T00:00:00Z",
        "download_url": f"https://s3.example/{path}?sig=abc",
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

    collected = await collect_run_outputs(client, "run-uuid")

    assert set(collected) == {METRICS, FIGURE}
    assert len(client.downloaded) == 2
    assert (
        collected[FIGURE] == f"content-of:https://s3.example/{FIGURE}?sig=abc".encode()
    )


async def test_collect_fails_when_listing_truncated():
    client = FakeSeyvalClient(
        outputs={"outputs": [_output(METRICS)], "truncated": True},
    )

    with pytest.raises(ValueError, match="truncated"):
        await collect_run_outputs(client, "run-uuid")

    # Nothing is imported from a partial listing.
    assert client.downloaded == []


async def test_collect_fails_when_no_results_files():
    client = FakeSeyvalClient(
        outputs={"outputs": [_output("wandb/debug.log")], "truncated": False},
    )

    with pytest.raises(ValueError, match="no files under"):
        await collect_run_outputs(client, "run-uuid")


async def test_collect_fails_when_download_url_missing():
    entry = _output(FIGURE)
    del entry["download_url"]
    client = FakeSeyvalClient(outputs={"outputs": [entry], "truncated": False})

    # Names the file rather than surfacing a bare KeyError from the gather.
    with pytest.raises(ValueError, match=r"figure\.pdf.*download_url"):
        await collect_run_outputs(client, "run-uuid")


async def test_collect_fails_when_batch_too_large():
    client = FakeSeyvalClient(
        outputs={
            "outputs": [_output(FIGURE, size_bytes=MAX_TOTAL_BYTES + 1)],
            "truncated": False,
        }
    )

    with pytest.raises(ValueError, match="import limit"):
        await collect_run_outputs(client, "run-uuid")


# --------------------------------------------------
# resolve_execution_id
# --------------------------------------------------


def _run(experiment_id: str, run_id: str, status: str = "completed") -> dict:
    return {"experiment_id": experiment_id, "run_id": run_id, "status": status}


async def test_resolve_picks_newest_completed_run_for_the_mode():
    client = FakeSeyvalClient(
        runs=[
            # Newest first, as Seyval lists them.
            _run("run_1_full", "newest", status="running"),
            _run("run_1_full", "wanted"),
            _run("run_1_full", "older"),
            _run("run_1_sanity", "sanity-run"),
        ]
    )

    execution_id = await resolve_execution_id(client, GITHUB_CONFIG, "run-1", "full")

    assert execution_id == "wanted"


async def test_resolve_does_not_cross_modes():
    client = FakeSeyvalClient(runs=[_run("run_1_sanity", "sanity-run")])

    with pytest.raises(ValueError, match="run_1_full"):
        await resolve_execution_id(client, GITHUB_CONFIG, "run-1", "full")


async def test_resolve_error_points_at_execution_id():
    client = FakeSeyvalClient(runs=[])

    with pytest.raises(ValueError, match="execution_id"):
        await resolve_execution_id(client, GITHUB_CONFIG, "run-1", "full")


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


async def test_subgraph_commits_downloaded_outputs_as_binary():
    seyval_client = FakeSeyvalClient(
        outputs={
            "outputs": [_output(METRICS), _output(FIGURE), _output("wandb/debug.log")],
            "truncated": False,
        },
        runs=[_run("run_1_full", "seyval-run-uuid")],
    )
    blobs: list[dict] = []

    result = await (
        ImportRunOutputsSubgraph(
            seyval_client=seyval_client,
            github_client=_github_client_capturing(blobs),
            run_stage=RunStage.FULL,
        )
        .build_graph()
        .ainvoke({"github_config": GITHUB_CONFIG, "run_id": "run-1"})
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
    assert f"content-of:https://s3.example/{FIGURE}?sig=abc".encode() in committed

    text_blobs = [b for b in blobs if b["encoding"] == "utf-8"]
    assert len(text_blobs) == 1
    manifest = json.loads(text_blobs[0]["content"])
    assert manifest["dirs"]["run-1"] == {
        "execution_id": "seyval-run-uuid",
        "commit_hash": SEYVAL_RUN_COMMIT,
    }


async def test_subgraph_uses_explicit_execution_id_without_lookup():
    seyval_client = FakeSeyvalClient(
        outputs={"outputs": [_output(METRICS)], "truncated": False},
        runs=[],  # a lookup would fail
    )

    result = await (
        ImportRunOutputsSubgraph(
            seyval_client=seyval_client,
            github_client=_github_client_capturing([]),
            execution_id="explicit-run-uuid",
        )
        .build_graph()
        .ainvoke({"github_config": GITHUB_CONFIG, "run_id": "run-1"})
    )

    assert result["execution_id"] == "explicit-run-uuid"
