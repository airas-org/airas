"""Batch-commit behaviour of GithubClient (Git Data API).

The client takes its HTTP sessions by DI, so the whole commit sequence
(branch -> blobs -> tree -> commit -> ref) is driven through an
httpx.MockTransport and every request body is captured for assertions.
"""

import base64
import json

import httpx
import pytest

from airas.infra.github_client import (
    MAX_BLOB_BYTES,
    GithubClient,
    GithubClientFatalError,
)

OWNER = "airas-org"
REPO = "experiment-repo"
BRANCH = "main"

BASE_COMMIT_SHA = "c" * 40
BASE_TREE_SHA = "t" * 40
NEW_TREE_SHA = "n" * 40
NEW_COMMIT_SHA = "d" * 40

# A real (tiny) PNG: bytes that are not valid UTF-8, so a text-only path
# would fail loudly rather than silently mangle them.
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


class RequestLog:
    """Captured requests, keyed by the API they hit."""

    def __init__(self) -> None:
        self.blobs: list[dict] = []
        self.trees: list[dict] = []
        self.commits: list[dict] = []
        self.refs: list[dict] = []


def _make_handler(log: RequestLog):
    """Serve the five endpoints a batch commit walks through."""

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        body = json.loads(request.content) if request.content else {}

        if request.method == "GET" and path.endswith(f"/branches/{BRANCH}"):
            return httpx.Response(
                200,
                json={
                    "commit": {
                        "sha": BASE_COMMIT_SHA,
                        "commit": {"tree": {"sha": BASE_TREE_SHA}},
                    }
                },
            )

        if request.method == "POST" and path.endswith("/git/blobs"):
            log.blobs.append(body)
            # A distinct sha per blob, so a path/sha mix-up is detectable.
            return httpx.Response(201, json={"sha": f"blob{len(log.blobs)}"})

        if request.method == "POST" and path.endswith("/git/trees"):
            log.trees.append(body)
            return httpx.Response(201, json={"sha": NEW_TREE_SHA})

        if request.method == "POST" and path.endswith("/git/commits"):
            log.commits.append(body)
            return httpx.Response(201, json={"sha": NEW_COMMIT_SHA})

        if request.method == "PATCH" and "/git/refs/" in path:
            log.refs.append(body)
            return httpx.Response(200, json={"ref": path})

        raise AssertionError(f"Unexpected request: {request.method} {path}")

    return handler


@pytest.fixture
def log() -> RequestLog:
    return RequestLog()


@pytest.fixture
def async_client(log: RequestLog) -> GithubClient:
    transport = httpx.MockTransport(_make_handler(log))
    return GithubClient(
        github_token="test-token",
        async_session=httpx.AsyncClient(transport=transport),
    )


@pytest.fixture
def sync_client(log: RequestLog) -> GithubClient:
    transport = httpx.MockTransport(_make_handler(log))
    return GithubClient(
        github_token="test-token",
        sync_session=httpx.Client(transport=transport),
    )


def _blob_by_encoding(log: RequestLog, encoding: str) -> list[dict]:
    return [blob for blob in log.blobs if blob["encoding"] == encoding]


def _tree_paths(log: RequestLog) -> dict[str, str]:
    """path -> blob sha, from the single tree that was created."""
    assert len(log.trees) == 1
    return {entry["path"]: entry["sha"] for entry in log.trees[0]["tree"]}


# --------------------------------------------------
# Text-only: existing behaviour must be untouched
# --------------------------------------------------


async def test_acommit_text_files_use_utf8(async_client: GithubClient, log: RequestLog):
    ok = await async_client.acommit_multiple_files(
        OWNER,
        REPO,
        BRANCH,
        files={"src/main.py": "print('hello')\n", "README.md": "# Title\n"},
        commit_message="Add text files",
    )

    assert ok is True
    assert len(log.blobs) == 2
    assert all(blob["encoding"] == "utf-8" for blob in log.blobs)
    # Raw string, not base64.
    assert {blob["content"] for blob in log.blobs} == {
        "print('hello')\n",
        "# Title\n",
    }
    assert log.commits[0]["parents"] == [BASE_COMMIT_SHA]
    assert log.trees[0]["base_tree"] == BASE_TREE_SHA
    assert log.refs[0]["sha"] == NEW_COMMIT_SHA


def test_commit_text_files_use_utf8(sync_client: GithubClient, log: RequestLog):
    ok = sync_client.commit_multiple_files(
        OWNER,
        REPO,
        BRANCH,
        files={"src/main.py": "print('hello')\n", "README.md": "# Title\n"},
        commit_message="Add text files",
    )

    assert ok is True
    assert len(log.blobs) == 2
    assert all(blob["encoding"] == "utf-8" for blob in log.blobs)


# --------------------------------------------------
# Binary
# --------------------------------------------------


async def test_acommit_binary_file_uses_base64(
    async_client: GithubClient, log: RequestLog
):
    await async_client.acommit_multiple_files(
        OWNER,
        REPO,
        BRANCH,
        files={".research/results/run-1/figure.png": PNG_BYTES},
        commit_message="Add figure",
    )

    assert len(log.blobs) == 1
    blob = log.blobs[0]
    assert blob["encoding"] == "base64"
    # Round-trips to the exact original bytes.
    assert base64.b64decode(blob["content"]) == PNG_BYTES


def test_commit_binary_file_uses_base64(sync_client: GithubClient, log: RequestLog):
    sync_client.commit_multiple_files(
        OWNER,
        REPO,
        BRANCH,
        files={".research/results/run-1/figure.png": PNG_BYTES},
        commit_message="Add figure",
    )

    assert len(log.blobs) == 1
    assert log.blobs[0]["encoding"] == "base64"
    assert base64.b64decode(log.blobs[0]["content"]) == PNG_BYTES


# --------------------------------------------------
# Mixed text + binary in one commit
# --------------------------------------------------


async def test_acommit_mixed_files_in_single_commit(
    async_client: GithubClient, log: RequestLog
):
    metrics = '{"accuracy": 0.91}'
    files: dict[str, str | bytes] = {
        ".research/results/run-1/metrics.json": metrics,
        ".research/results/run-1/figure.png": PNG_BYTES,
        ".research/results/run-1/notes.md": "# Notes\n",
    }

    ok = await async_client.acommit_multiple_files(
        OWNER, REPO, BRANCH, files=files, commit_message="Import run outputs"
    )

    assert ok is True
    # One commit, one tree, one ref update — regardless of file count.
    assert len(log.blobs) == 3
    assert len(log.trees) == 1
    assert len(log.commits) == 1
    assert len(log.refs) == 1

    assert len(_blob_by_encoding(log, "base64")) == 1
    assert len(_blob_by_encoding(log, "utf-8")) == 2

    # Every path made it into the tree, each with a distinct blob sha.
    paths = _tree_paths(log)
    assert set(paths) == set(files)
    assert len(set(paths.values())) == 3


async def test_acommit_pairs_paths_with_their_own_blob(
    async_client: GithubClient, log: RequestLog
):
    """The tree entry for a path must carry that path's blob sha.

    The handler hands out `blob1`, `blob2`, ... in request order, so
    comparing against the order the blob contents arrived catches any
    drift between the blob list and the tree entries.
    """
    files: dict[str, str | bytes] = {
        "a.txt": "aaa",
        "b.png": PNG_BYTES,
        "c.txt": "ccc",
        "d.png": PNG_BYTES + b"\x00",
    }

    await async_client.acommit_multiple_files(
        OWNER, REPO, BRANCH, files=files, commit_message="Mixed"
    )

    paths = _tree_paths(log)
    for path, expected in files.items():
        blob = log.blobs[int(paths[path].removeprefix("blob")) - 1]
        if isinstance(expected, bytes):
            assert base64.b64decode(blob["content"]) == expected
        else:
            assert blob["content"] == expected


# --------------------------------------------------
# Guards
# --------------------------------------------------


async def test_acommit_rejects_oversized_blob(async_client: GithubClient):
    # The error must name the offending file, not just the batch.
    with pytest.raises(GithubClientFatalError, match=r"too large.*results/big\.bin"):
        await async_client.acommit_multiple_files(
            OWNER,
            REPO,
            BRANCH,
            files={
                "notes.md": "small\n",
                ".research/results/big.bin": b"\x00" * (MAX_BLOB_BYTES + 1),
            },
            commit_message="Too big",
        )


def test_commit_rejects_oversized_blob(sync_client: GithubClient):
    with pytest.raises(GithubClientFatalError, match=r"too large.*results/big\.bin"):
        sync_client.commit_multiple_files(
            OWNER,
            REPO,
            BRANCH,
            files={".research/results/big.bin": b"\x00" * (MAX_BLOB_BYTES + 1)},
            commit_message="Too big",
        )
