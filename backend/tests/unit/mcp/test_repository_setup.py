"""The MCP tools are adapters: they build the config and hand off."""

from typing import Any

import pytest

from airas.core.types.github import GitHubConfig
from airas.mcp.tools import repository as repository_tools


async def test_prepare_repository_forwards_every_argument(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, Any] = {}

    async def _prepare(config: GitHubConfig, **kwargs: Any) -> dict[str, Any]:
        seen["config"] = config
        seen.update(kwargs)
        return {"ok": True}

    monkeypatch.setattr(repository_tools, "_github_client", lambda: "client")
    monkeypatch.setattr(
        repository_tools.prepare_repository_usecase, "prepare_repository", _prepare
    )

    result = await repository_tools.prepare_repository(
        "o",
        "r",
        branch_name="research",
        is_private=True,
        protected_branch="main",
    )

    assert result == {"ok": True}
    assert seen["config"] == GitHubConfig(
        github_owner="o", repository_name="r", branch_name="research"
    )
    assert seen["github_client"] == "client"
    assert (seen["is_private"], seen["protected_branch"]) == (True, "main")


async def test_set_github_actions_secrets_wraps_the_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _set(config: GitHubConfig, **kwargs: Any) -> bool:
        assert kwargs["secret_names"] == ["SEYVAL_API_KEY"]
        return True

    monkeypatch.setattr(repository_tools, "_github_client", lambda: "client")
    monkeypatch.setattr(
        repository_tools.set_github_actions_secrets_usecase,
        "set_github_actions_secrets",
        _set,
    )

    result = await repository_tools.set_github_actions_secrets(
        "o", "r", secret_names=["SEYVAL_API_KEY"]
    )
    assert result == {"secrets_set": True}
