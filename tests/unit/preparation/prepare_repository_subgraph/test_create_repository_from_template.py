from typing import Any

import pytest

from airas.preparation.prepare_repository_subgraph.nodes.create_repository_from_template import (
    create_repository_from_template,
)


class DummyGithubClient:
    _next_return: Any = None

    def __init__(self):
        pass

    def create_repository_from_template(
        self,
        github_owner: str,
        repository_name: str,
        template_owner: str,
        template_repo: str,
        include_all_branches: bool = True,
        private: bool = False,
    ) -> Any:
        if isinstance(self._next_return, Exception):
            raise self._next_return
        return self._next_return

@pytest.fixture
def dummy_github_client():
    return DummyGithubClient

@pytest.fixture
def sample_inputs_create() -> dict[str, Any]:
    return {
        "github_owner": "test-owner",
        "repository_name": "test-repo",
        "template_owner": "tpl-owner",
        "template_repo": "tpl-repo",
        "include_all_branches": True,
        "private": False,
    }

@pytest.mark.parametrize(
    "dummy_return, expected_result, should_raise",
    [
        (True, True, False),
        (False, False, False),
        (Exception("template error"), None, True),
    ],
)
def test_create_repository_from_template(
    sample_inputs_create,
    dummy_return,
    expected_result,
    should_raise,
    dummy_github_client,
):
    client = dummy_github_client()
    client._next_return = dummy_return

    if should_raise:
        with pytest.raises(Exception):  # noqa: B017
            create_repository_from_template(**sample_inputs_create, client=client)
    else:
        result = create_repository_from_template(**sample_inputs_create, client=client)
        assert result is expected_result
