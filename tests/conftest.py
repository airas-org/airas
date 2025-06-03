from typing import Any

import pytest


class DummyLLMFacadeClient:
    _next_return: Any = None

    def __init__(self, llm_name: str):
        self.llm_name = llm_name

    def generate(self, message: str) -> tuple[Any, float]:
        if isinstance(self._next_return, tuple):
            return self._next_return
        return None, 0.0

    def structured_outputs(
        self, *, message, data_model
    ) -> tuple[dict[Any, Any] | None, float]:
        if isinstance(self._next_return, dict):
            return self._next_return, 0.0
        return None, 0.0

@pytest.fixture
def dummy_llm_facade_client():
    return DummyLLMFacadeClient


class DummyGithubClient:
    _next_return: Any = None
    _raise_error: Exception | None = None

    def __init__(self):
        pass

    def get_branch(
        self, github_owner: str, repository_name: str, branch_name: str
    ) -> Any:
        return self._next_return

    def get_repository(self, github_owner: str, repository_name: str) -> Any:
        if self._raise_error:
            raise self._raise_error
        return self._next_return
    
    def create_branch(
        self, 
        github_owner: str, 
        repository_name: str, 
        branch_name: str, 
        from_sha: str, 
    ) -> Any:
        return self._next_return
    
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
