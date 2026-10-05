from typing import cast

import pytest

from airas.core import credentials
from airas.core.types.github import GitHubConfig
from airas.infra.github.nodes.set_github_actions_secrets import (
    set_github_actions_secrets,
)
from airas.infra.github_client import GithubClient

CONFIG = GitHubConfig(github_owner="o", repository_name="r", branch_name="main")


class FakeGithubClient:
    def __init__(self) -> None:
        self.set: list[str] = []

    def get_repository_public_key(self, github_owner, repository_name):
        return {"key_id": "k", "key": "a" * 43 + "="}

    def create_or_update_repository_secret(self, **kw):
        self.set.append(kw["secret_name"])
        return True


def test_the_ci_secrets_are_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GH_PERSONAL_ACCESS_TOKEN", "ghp_x")
    monkeypatch.delenv("SEYVAL_API_KEY", raising=False)
    with pytest.raises(ValueError, match="SEYVAL_API_KEY"):
        set_github_actions_secrets(CONFIG, cast(GithubClient, FakeGithubClient()))


def test_the_default_set_is_the_credentials_file_plus_the_ci_secrets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GH_PERSONAL_ACCESS_TOKEN", "ghp_x")
    monkeypatch.setenv("SEYVAL_API_KEY", "sk_x")
    monkeypatch.setenv("MY_LLM_KEY", "v")
    monkeypatch.setattr(credentials, "load_credentials", lambda: {"MY_LLM_KEY": "v"})
    client = FakeGithubClient()
    assert set_github_actions_secrets(CONFIG, cast(GithubClient, client)) is True
    assert client.set == ["GH_PERSONAL_ACCESS_TOKEN", "MY_LLM_KEY", "SEYVAL_API_KEY"]


def test_an_explicit_list_requires_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GH_PERSONAL_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("SEYVAL_API_KEY", raising=False)
    monkeypatch.setenv("ONLY_THIS", "v")
    client = FakeGithubClient()
    assert set_github_actions_secrets(
        CONFIG, cast(GithubClient, client), secret_names=["ONLY_THIS"]
    )
    assert client.set == ["ONLY_THIS"]
