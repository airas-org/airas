import pytest
from airas.preparation.prepare_repository_subgraph.nodes.create_branch import create_branch

@pytest.fixture
def sample_inputs() -> dict[str, str]:
    return {
        "github_owner": "auto-res2",
        "repository_name": "test-repo",
        "branch_name": "new-branch",
        "main_sha": "abc123",
    }

@pytest.mark.parametrize(
    "dummy_return, should_raise",
    [
        (True, False),
        (False, True),
        (None, True),
    ],
)
def test_create_branch(
    sample_inputs: dict[str, str],
    dummy_return,
    should_raise,
    dummy_github_client,
):
    client = dummy_github_client()
    client._next_return = dummy_return

    if should_raise:
        with pytest.raises(RuntimeError) as excinfo:
            create_branch(
                github_owner=sample_inputs["github_owner"],
                repository_name=sample_inputs["repository_name"],
                branch_name=sample_inputs["branch_name"],
                main_sha=sample_inputs["main_sha"],
                client=client,
            )
        assert f"Failed to create branch '{sample_inputs['branch_name']}'" in str(excinfo.value)
    else:
        result = create_branch(
            github_owner=sample_inputs["github_owner"],
            repository_name=sample_inputs["repository_name"],
            branch_name=sample_inputs["branch_name"],
            main_sha=sample_inputs["main_sha"],
            client=client,
        )
        assert result is True 
