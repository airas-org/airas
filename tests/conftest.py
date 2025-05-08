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

    def __init__(self):
        pass

    def check_branch_existence(
        self, github_owner: str, repository_name: str, branch_name: str
    ) -> Any:
        return self._next_return

    def get_repository(
        self, github_owner: str, repository_name: str
    ) -> Any:
        return self._next_return
    
    def create_branch(
        self, 
        github_owner: str, 
        repository_name: str, 
        branch_name: str, 
        from_sha: str, 
    ) -> Any:
        return self._next_return
    
    def fork_repository(
        self, 
        repository_name: str, 
        device_type: str, 
        organization: str, 
    ) -> Any:
        return self._next_return

@pytest.fixture
def dummy_github_client():
    return DummyGithubClient
