import pytest

from airas.preparation.prepare_repository_subgraph.nodes.fork_repository import fork_repository


@pytest.fixture
def sample_inputs_fork() -> dict[str, str]:
    return {
        "repository_name": "test-repo",
        "device_type": "cpu",
        "organization": "",
    }

@pytest.mark.parametrize(
    "dummy_return, should_raise",
    [
        (True, False),
        (False, True),
        (None, True),
    ],
)
def test_fork_repository_di(
    sample_inputs_fork: dict[str, str],
    dummy_return,
    should_raise,
    dummy_github_client,
):
    client = dummy_github_client()
    client._next_return = dummy_return

    if should_raise:
        with pytest.raises(RuntimeError) as excinfo:
            fork_repository(
                repository_name=sample_inputs_fork["repository_name"],
                device_type=sample_inputs_fork["device_type"],
                organization=sample_inputs_fork["organization"],
                client=client,
            )
        assert "Fork of the repository failed" in str(excinfo.value)
    else:
        result = fork_repository(
            repository_name=sample_inputs_fork["repository_name"],
            device_type=sample_inputs_fork["device_type"],
            organization=sample_inputs_fork["organization"],
            client=client,
        )
        assert result is True
