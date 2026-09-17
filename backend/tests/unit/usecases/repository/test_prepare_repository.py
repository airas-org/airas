"""Branch protection is setup whose absence is invisible: without it a red
CI run can simply be pushed past. Its failure may not abort the creation
(a repository that exists but is unprotected is still worth returning) but
may not pass unreported either."""

from typing import Any

import pytest

from airas.core.types.github import GitHubConfig
from airas.usecases.repository import prepare_repository as usecase
from airas.usecases.repository.nodes.protect_branch import REQUIRED_CHECK_NAMES

CONFIG = GitHubConfig(github_owner="o", repository_name="r", branch_name="main")


class _Recorder:
    def __init__(self) -> None:
        self.template_checks = 0
        self.protection: list[tuple[str, str, str, list[str]]] = []
        self.pages: list[tuple[str, str]] = []


class _FakeClient:
    def __init__(self, recorder: _Recorder, pages_error: str | None = None) -> None:
        self._recorder = recorder
        self._pages_error = pages_error

    async def aenable_pages_from_actions(self, owner: str, repo: str) -> bool:
        if self._pages_error:
            raise RuntimeError(self._pages_error)
        self._recorder.pages.append((owner, repo))
        return True


@pytest.fixture
def recorder(monkeypatch: pytest.MonkeyPatch) -> _Recorder:
    """The repository and branch already exist; only the CI setup runs."""
    rec = _Recorder()

    def _exists(**_kwargs: Any) -> bool:
        rec.template_checks += 1
        return True

    async def _protect(config: GitHubConfig, branch: str, *, github_client: Any):
        rec.protection.append(
            (config.github_owner, config.repository_name, branch, REQUIRED_CHECK_NAMES)
        )
        return True, True

    monkeypatch.setattr(usecase, "check_repository_from_template", _exists)
    monkeypatch.setattr(usecase, "retrieve_branch_sha", lambda **_: "sha")
    monkeypatch.setattr(usecase, "protect_branch", _protect)
    return rec


async def _prepare(
    recorder: _Recorder, config: GitHubConfig = CONFIG, **kwargs: Any
) -> dict[str, Any]:
    client = kwargs.pop("client", None) or _FakeClient(recorder)
    return await usecase.prepare_repository(config, github_client=client, **kwargs)


async def test_setup_protects_the_branch_and_returns_the_location(
    recorder: _Recorder,
) -> None:
    result = await _prepare(recorder)

    assert result["clone_url"] == "https://github.com/o/r.git"
    assert result["html_url"] == "https://github.com/o/r"
    assert result["is_branch_ready"] is True
    assert result["branch_protected"] is True
    assert result["merge_settings_updated"] is True
    assert result["pages_enabled"] is True
    assert result["warnings"] == []
    assert recorder.pages == [("o", "r")]
    # The required checks are the gates' job names in the template workflows: a
    # different string would be required forever and never reported.
    assert recorder.protection == [("o", "r", "main", REQUIRED_CHECK_NAMES)]


async def test_the_working_branch_is_protected_by_default(recorder: _Recorder) -> None:
    config = GitHubConfig(github_owner="o", repository_name="r", branch_name="research")
    result = await _prepare(recorder, config)
    assert recorder.protection[0][2] == "research"
    assert result["protected_branch"] == "research"


async def test_the_protected_branch_can_differ_from_the_working_branch(
    recorder: _Recorder,
) -> None:
    config = GitHubConfig(github_owner="o", repository_name="r", branch_name="research")
    await _prepare(recorder, config, protected_branch="main")
    assert recorder.protection[0][2] == "main"


async def test_failed_protection_is_reported_but_does_not_lose_the_repository(
    recorder: _Recorder, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _boom(*_args: Any, **_kwargs: Any) -> tuple[bool, bool]:
        raise RuntimeError("403 admin rights required")

    monkeypatch.setattr(usecase, "protect_branch", _boom)
    result = await _prepare(recorder)

    assert result["is_repository_ready"] is True
    assert result["clone_url"] == "https://github.com/o/r.git"
    assert result["branch_protected"] is False
    assert result["protected_branch"] is None
    assert any("403" in w for w in result["warnings"])
    assert any("re-run prepare_repository" in w for w in result["warnings"])


async def test_rerunning_is_the_repair_path(recorder: _Recorder) -> None:
    """No separate repair tool: a second run reaches the same code."""
    await _prepare(recorder)
    await _prepare(recorder)
    assert recorder.template_checks == 2
    assert len(recorder.protection) == 2


async def test_pages_that_cannot_be_enabled_are_reported_not_fatal(
    recorder: _Recorder,
) -> None:
    client = _FakeClient(
        recorder, pages_error="Upgrade to GitHub Pro or make this repository public"
    )
    result = await _prepare(recorder, client=client)
    assert result["is_repository_ready"] is True
    assert result["pages_enabled"] is False
    assert any("make this repository public" in w for w in result["warnings"])
