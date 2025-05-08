import pytest

from airas.preparation.prepare_repository_subgraph.nodes.check_github_repository import (
    check_github_repository,
)


@pytest.fixture
def sample_inputs() -> dict[str, str]:
    return {
        "github_owner": "auto-res2",
        "repository_name": "test-repo",
    }


@pytest.mark.parametrize(
    "dummy_return, expected",
    [
        ({"id": "repo-id"}, True), 
        (None, False),
    ],
)
def test_check_github_repository(
    sample_inputs: dict[str, str],
    dummy_return,
    expected,
    dummy_github_client,
):
    client = dummy_github_client()
    client._next_return = dummy_return

    result = check_github_repository(
        github_owner=sample_inputs["github_owner"],
        repository_name=sample_inputs["repository_name"],
        client=client,
    )
    assert result is expected
