import pytest

from airas.preparation.prepare_repository_subgraph.nodes.retrieve_main_branch_sha import retrieve_main_branch_sha


@pytest.fixture
def sample_inputs_retrieve() -> dict[str, str]:
    return {
        "github_owner": "auto-res2",
        "repository_name": "test-repo",
    }

@pytest.mark.parametrize(
    "dummy_return, expected, should_raise",
    [
        ({"commit": {"sha": "abc123"}}, "abc123", False),
        (None, None, True),
        ({}, None, True),
        ({"commit": {}}, None, True),
        ({"commit": {"sha": ""}}, None, True),
    ],
)
def test_retrieve_main_branch_sha_di(
    sample_inputs_retrieve: dict[str, str],
    dummy_return,
    expected,
    should_raise,
    dummy_github_client,
):
    client = dummy_github_client()
    client._next_return = dummy_return

    if should_raise:
        with pytest.raises(RuntimeError) as excinfo:
            retrieve_main_branch_sha(
                github_owner=sample_inputs_retrieve["github_owner"],
                repository_name=sample_inputs_retrieve["repository_name"],
                client=client,
            )
        assert (
            "SHA for 'main' branch of "
            f"{sample_inputs_retrieve['github_owner']}/"
            f"{sample_inputs_retrieve['repository_name']}"
        ) in str(excinfo.value)
    else:
        result = retrieve_main_branch_sha(
            github_owner=sample_inputs_retrieve["github_owner"],
            repository_name=sample_inputs_retrieve["repository_name"],
            client=client,
        )
        assert result == expected