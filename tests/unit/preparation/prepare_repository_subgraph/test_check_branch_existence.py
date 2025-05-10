import pytest

from airas.preparation.prepare_repository_subgraph.nodes.check_branch_existence import (
    check_branch_existence,
)


@pytest.fixture
def sample_inputs() -> dict[str, str]:
    return {
        "github_owner": "auto-res2",
        "repository_name": "test-repo",
        "branch_name": "feature-xyz",
    }

@pytest.mark.parametrize(
    "dummy_return, expected",
    [
        ({"commit": {"sha": "abc123def"}}, "abc123def"),
        (None, None),
        ({}, None),
    ],
)
def test_check_branch_existence(
    sample_inputs: dict[str, str],
    dummy_return: str | None,
    expected: str | None,
    dummy_github_client,
):
    client = dummy_github_client()
    client._next_return = dummy_return

    result = check_branch_existence(
        github_owner=sample_inputs["github_owner"],
        repository_name=sample_inputs["repository_name"],
        branch_name=sample_inputs["branch_name"],
        client=client,
    )

    assert result == expected