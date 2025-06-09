import pytest

from airas.preparation.prepare_repository_subgraph.nodes.check_repository_from_template import (
    check_repository_from_template,
)
from airas.utils.api_client.github_client import GithubClientError


@pytest.fixture
def sample_inputs():
    return {
        "github_owner": "auto-res2",
        "repository_name": "test-repo",
        "template_owner": "auto-res2",
        "template_repo": "template-repo",
    }

@pytest.mark.parametrize(
    "response_data, expected_result, expected_exception",
    [
        (
            {"template_repository": {"owner": {"login": "auto-res2"}, "name": "template-repo"}},
            True,
            None,
        ),
        (
            {"template_repository": {"owner": {"login": "someone-else"}, "name": "other-template"}},
            None,
            ValueError,
        ),
        (
            {"template_repository": None},
            None,
            ValueError,
        ),
    ],
)
def test_check_repository_from_template_success_and_template_mismatch(
    sample_inputs,
    response_data,
    expected_result,
    expected_exception,
    dummy_github_client,
):
    client = dummy_github_client()
    client._next_return = response_data

    if expected_exception:
        with pytest.raises(expected_exception):
            check_repository_from_template(
                github_owner=sample_inputs["github_owner"],
                repository_name=sample_inputs["repository_name"],
                template_owner=sample_inputs["template_owner"],
                template_repo=sample_inputs["template_repo"],
                client=client,
            )
    else:
        result = check_repository_from_template(
            github_owner=sample_inputs["github_owner"],
            repository_name=sample_inputs["repository_name"],
            template_owner=sample_inputs["template_owner"],
            template_repo=sample_inputs["template_repo"],
            client=client,
        )
        assert result == expected_result


def test_check_repository_from_template_repository_not_exist(sample_inputs, dummy_github_client):
    client = dummy_github_client()
    client._raise_error = GithubClientError("Repository not found")

    result = check_repository_from_template(
        github_owner=sample_inputs["github_owner"],
        repository_name=sample_inputs["repository_name"],
        template_owner=sample_inputs["template_owner"],
        template_repo=sample_inputs["template_repo"],
        client=client,
    )
    assert result is False