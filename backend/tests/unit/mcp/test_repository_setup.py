"""Repository setup, where enforcement is either configured or silently not.

`prepare_repository` provisions the Actions secrets and protects the
default branch because both are setup whose absence is invisible: without
`SEYVAL_API_KEY` the provenance cross-check degrades to a skip rather than
a failure, and without branch protection a red CI run can simply be pushed
past. Neither may abort the creation — a repository that exists but is
unconfigured is still worth returning — but neither may pass unreported
either, which is what these tests hold.
"""

from typing import Any

import pytest

from airas.mcp import server


class _Recorder:
    def __init__(self) -> None:
        self.secrets: list[tuple[str, str, str]] = []
        self.protection: list[tuple[str, str, str, list[str]]] = []


@pytest.fixture
def recorder(monkeypatch: pytest.MonkeyPatch) -> _Recorder:
    """Stand in for the repository creation and both configuration calls."""
    rec = _Recorder()

    class _FakeSubgraph:
        def __init__(self, github_client: Any, is_github_repo_private: bool) -> None:
            pass

        def build_graph(self) -> "_FakeSubgraph":
            return self

        async def ainvoke(self, _state: dict) -> dict:
            return {
                "is_repository_ready": True,
                "is_branch_ready": True,
                "html_url": "https://github.com/o/r",
                "clone_url": "https://github.com/o/r.git",
            }

    async def _secrets(owner: str, repo: str, branch: str, names=None) -> bool:
        rec.secrets.append((owner, repo, branch))
        return True

    async def _protect(
        owner: str, repo: str, branch: str, checks: list[str]
    ) -> tuple[bool, bool]:
        rec.protection.append((owner, repo, branch, checks))
        return True, True

    monkeypatch.setattr(server, "PrepareRepositorySubgraph", _FakeSubgraph)
    monkeypatch.setattr(server, "_github_client", lambda: object())
    monkeypatch.setattr(server, "_apply_secrets", _secrets)
    monkeypatch.setattr(server, "_apply_branch_protection", _protect)
    return rec


async def test_setup_configures_secrets_and_protection(recorder: _Recorder) -> None:
    result = await server.prepare_repository("o", "r")

    assert result["secrets_set"] is True
    assert result["branch_protected"] is True
    assert result["merge_settings_updated"] is True
    assert result["warnings"] == []
    assert recorder.secrets == [("o", "r", "main")]
    # The required check is the record gate's job name in the template
    # workflow: a different string would be required forever and never
    # reported, which blocks the branch instead of guarding it.
    assert recorder.protection == [("o", "r", "main", [server.RECORD_GATE_CHECK_NAME])]


async def test_the_protected_branch_can_differ_from_the_working_branch(
    recorder: _Recorder,
) -> None:
    await server.prepare_repository(
        "o", "r", branch_name="research", protected_branch="main"
    )
    assert recorder.secrets == [("o", "r", "research")]
    assert recorder.protection[0][2] == "main"


async def test_failed_protection_is_reported_but_does_not_lose_the_repository(
    recorder: _Recorder, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _boom(*_args: Any, **_kwargs: Any) -> tuple[bool, bool]:
        raise RuntimeError("403 admin rights required")

    monkeypatch.setattr(server, "_apply_branch_protection", _boom)
    result = await server.prepare_repository("o", "r")

    # The repository was created; throwing that away would help nobody.
    assert result["is_repository_ready"] is True
    assert result["clone_url"] == "https://github.com/o/r.git"
    # But it is not enforcing anything, and says so.
    assert result["branch_protected"] is False
    assert result["protected_branch"] is None
    assert any("403" in w for w in result["warnings"])
    assert any("protect_branch" in w for w in result["warnings"])


async def test_failed_secrets_warn_that_the_check_will_look_green(
    recorder: _Recorder, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The dangerous part is that the failure mode is a skip, not an error."""

    async def _boom(*_args: Any, **_kwargs: Any) -> bool:
        raise RuntimeError("no token")

    monkeypatch.setattr(server, "_apply_secrets", _boom)
    result = await server.prepare_repository("o", "r")

    assert result["secrets_set"] is False
    assert any("skipped rather than fail" in w for w in result["warnings"])
    # A failed secret must not stop the branch from being protected.
    assert result["branch_protected"] is True


async def test_configure_ci_can_be_declined(recorder: _Recorder) -> None:
    result = await server.prepare_repository("o", "r", configure_ci=False)

    assert result["secrets_set"] is False
    assert result["branch_protected"] is False
    assert result["warnings"] == []
    assert recorder.secrets == []
    assert recorder.protection == []


async def test_standalone_tools_reach_the_same_code(recorder: _Recorder) -> None:
    """The repair path and the setup path must not drift apart."""
    assert (await server.set_github_actions_secrets("o", "r"))["secrets_set"]
    assert recorder.secrets == [("o", "r", "main")]

    protect = await server.protect_branch("o", "r")
    assert protect["branch_protected"] is True
    assert protect["required_checks"] == [server.RECORD_GATE_CHECK_NAME]
    assert recorder.protection[0][3] == [server.RECORD_GATE_CHECK_NAME]
