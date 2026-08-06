"""Figure paths must survive as paths, not collapse to bare filenames.

The LaTeX collectors place `.research/results/<rest>` at `images/<rest>`,
so a figure reported as `plot.pdf` sends the paper to `images/plot.pdf`
while the file sits at `images/run-1/plot.pdf`. Two runs writing the same
filename collide the same way. Both failures still produce a PDF, so
nothing downstream notices.
"""

import pytest

from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClientFatalError
from airas.usecases.executors.fetch_experiment_results_subgraph.nodes.fetch_results import (
    _fetch_figure_paths,
    _image_prefix,
    fetch_results,
)

GITHUB_CONFIG = GitHubConfig(
    github_owner="airas-org",
    repository_name="experiment-repo",
    branch_name="main",
)

RESULTS_DIR = ".research/results"


def _file(name: str) -> dict:
    return {"name": name, "type": "file"}


def _dir(name: str) -> dict:
    return {"name": name, "type": "dir"}


class FakeGithubClient:
    """Serves a fixed directory tree through the contents API shape.

    Absence and refusal are raised the way GithubClient raises them: the
    same exception type, told apart only by `status_code`.
    """

    def __init__(self, tree: dict[str, list[dict]], forbidden: set[str] | None = None):
        self._tree = tree
        self._forbidden = forbidden or set()
        self.requested: list[str] = []

    async def aget_repository_content(
        self, github_owner: str, repository_name: str, file_path: str, branch_name: str
    ):
        self.requested.append(file_path)
        if file_path in self._forbidden:
            raise GithubClientFatalError(
                f"Access forbidden (403): {file_path}", status_code=403
            )
        if file_path in self._tree:
            return self._tree[file_path]
        raise GithubClientFatalError(
            f"Resource not found (404): {file_path}", status_code=404
        )


@pytest.mark.asyncio
async def test_listing_descends_into_subdirectories():
    client = FakeGithubClient(
        {
            f"{RESULTS_DIR}/run-1": [_file("metrics.json"), _dir("chart")],
            f"{RESULTS_DIR}/run-1/chart": [_file("loss.pdf"), _file("accuracy.pdf")],
        }
    )

    files = await _fetch_figure_paths(
        client,
        GITHUB_CONFIG.github_owner,
        GITHUB_CONFIG.repository_name,
        f"{RESULTS_DIR}/run-1",
        GITHUB_CONFIG.branch_name,
    )

    assert sorted(files) == ["chart/accuracy.pdf", "chart/loss.pdf"]


@pytest.mark.asyncio
async def test_only_pdfs_are_reported_as_figures():
    """Descending recursively reaches everything a run writes, not just plots.

    The collectors copy `*.pdf` and nothing else, so a checkpoint reported
    as a figure sends the paper after an image that never exists.
    """
    client = FakeGithubClient(
        {
            f"{RESULTS_DIR}/run-1": [
                _file("metrics.json"),
                _file("loss.pdf"),
                _dir("checkpoints"),
                _dir("logs"),
            ],
            f"{RESULTS_DIR}/run-1/checkpoints": [_file("model.safetensors")],
            f"{RESULTS_DIR}/run-1/logs": [_file("train.log"), _file("stderr.txt")],
        }
    )

    files = await _fetch_figure_paths(
        client,
        GITHUB_CONFIG.github_owner,
        GITHUB_CONFIG.repository_name,
        f"{RESULTS_DIR}/run-1",
        GITHUB_CONFIG.branch_name,
    )

    assert files == ["loss.pdf"]


@pytest.mark.asyncio
async def test_listing_stops_at_the_depth_limit():
    tree = {f"{RESULTS_DIR}/run-1": [_dir("d1")]}
    path = f"{RESULTS_DIR}/run-1"
    for level in range(1, 7):
        path = f"{path}/d{level}"
        tree[path] = [_file(f"deep{level}.pdf"), _dir(f"d{level + 1}")]

    client = FakeGithubClient(tree)
    files = await _fetch_figure_paths(
        client,
        GITHUB_CONFIG.github_owner,
        GITHUB_CONFIG.repository_name,
        f"{RESULTS_DIR}/run-1",
        GITHUB_CONFIG.branch_name,
    )

    # Four levels below the root are listed; the fifth is never requested,
    # so a stray deep directory tree cannot fan out into unbounded API calls.
    assert files == [
        "d1/deep1.pdf",
        "d1/d2/deep2.pdf",
        "d1/d2/d3/deep3.pdf",
        "d1/d2/d3/d4/deep4.pdf",
    ]
    assert f"{RESULTS_DIR}/run-1/d1/d2/d3/d4/d5" not in client.requested


@pytest.mark.asyncio
async def test_same_filename_in_two_runs_stays_distinguishable():
    client = FakeGithubClient(
        {
            f"{RESULTS_DIR}/run-1": [_file("accuracy.pdf")],
            f"{RESULTS_DIR}/run-2": [_file("accuracy.pdf")],
            f"{RESULTS_DIR}/comparison": [],
        }
    )

    results = await fetch_results(
        client, GITHUB_CONFIG, run_ids=["run-1", "run-2"], results_dir=RESULTS_DIR
    )

    assert sorted(results.result_figures or []) == [
        "run-1/accuracy.pdf",
        "run-2/accuracy.pdf",
    ]


@pytest.mark.asyncio
async def test_diagram_directories_map_to_their_image_paths():
    client = FakeGithubClient(
        {
            f"{RESULTS_DIR}/run-1": [],
            f"{RESULTS_DIR}/comparison": [],
            f"{RESULTS_DIR}/diagram": [_file("architecture.pdf")],
            ".research/diagrams": [_file("legacy.pdf")],
        }
    )

    results = await fetch_results(
        client, GITHUB_CONFIG, run_ids=["run-1"], results_dir=RESULTS_DIR
    )

    # The legacy directory is merged into images/ flat; the current one sits
    # under results_dir and keeps its subpath. Both match the collectors.
    assert sorted(results.diagram_figures or []) == [
        "diagram/architecture.pdf",
        "legacy.pdf",
    ]


def test_image_prefix_matches_the_collector_mapping():
    assert _image_prefix(f"{RESULTS_DIR}/diagram", RESULTS_DIR) == "diagram/"
    assert _image_prefix(RESULTS_DIR, RESULTS_DIR) == ""
    assert _image_prefix(".research/diagrams", RESULTS_DIR) == ""


@pytest.mark.asyncio
async def test_missing_directory_yields_no_files():
    client = FakeGithubClient({})

    files = await _fetch_figure_paths(
        client,
        GITHUB_CONFIG.github_owner,
        GITHUB_CONFIG.repository_name,
        f"{RESULTS_DIR}/absent",
        GITHUB_CONFIG.branch_name,
    )

    assert files == []


@pytest.mark.asyncio
async def test_a_refused_directory_is_not_reported_as_an_empty_one():
    """A token without access must not read as "this run produced nothing".

    404 and 403 arrive as the same exception type; swallowing both turns a
    permission problem into a paper written with no figures and no warning.
    """
    client = FakeGithubClient(
        {f"{RESULTS_DIR}/run-1": [_file("accuracy.pdf")]},
        forbidden={f"{RESULTS_DIR}/run-1"},
    )

    with pytest.raises(GithubClientFatalError):
        await _fetch_figure_paths(
            client,
            GITHUB_CONFIG.github_owner,
            GITHUB_CONFIG.repository_name,
            f"{RESULTS_DIR}/run-1",
            GITHUB_CONFIG.branch_name,
        )
