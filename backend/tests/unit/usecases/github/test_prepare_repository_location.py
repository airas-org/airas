"""The caller is told to clone the repository, so it has to be told where.

`prepare_repository` returned `{"is_repository_ready": ..., "is_branch_ready":
...}` and nothing else — no URL, no clone command — while the next step in
every flow is `git clone`. The location had to be reassembled from the
owner and name that were passed in.
"""

from airas.core.types.github import GitHubConfig
from airas.usecases.github.prepare_repository_subgraph.prepare_repository_subgraph import (
    PrepareRepositorySubgraph,
)

GITHUB_CONFIG = GitHubConfig(
    github_owner="airas-org",
    repository_name="experiment-repo",
    branch_name="main",
)


def _finalize(**state) -> dict:
    subgraph = PrepareRepositorySubgraph.__new__(PrepareRepositorySubgraph)
    return subgraph._finalize_state({"github_config": GITHUB_CONFIG, **state})


def test_the_repository_location_is_returned():
    result = _finalize(is_repository_from_template=True, is_branch_created=True)

    assert result["clone_url"] == "https://github.com/airas-org/experiment-repo.git"
    assert result["html_url"] == "https://github.com/airas-org/experiment-repo"


def test_readiness_is_still_reported():
    ready = _finalize(is_repository_from_template=True, is_branch_already_exists=True)
    assert ready["is_repository_ready"] and ready["is_branch_ready"]

    unprepared = _finalize()
    assert not unprepared["is_repository_ready"]
    assert not unprepared["is_branch_ready"]
    # The location is reported either way; it is where the repository would
    # be, not a claim that it is ready.
    assert unprepared["clone_url"].endswith("experiment-repo.git")
