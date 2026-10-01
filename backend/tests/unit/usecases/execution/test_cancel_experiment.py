from typing import Any, cast

import httpx
import pytest

from airas.infra.github_client import GithubClient
from airas.infra.seyval_client import SeyvalClient
from airas.usecases.execution.cancel_experiment import cancel_experiment
from airas.usecases.execution.get_experiment_run_status import (
    get_experiment_run_status,
)


def _github_client(status_code: int) -> GithubClient:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/actions/runs/12345/cancel")
        return httpx.Response(status_code)

    return GithubClient(
        github_token="t",
        async_session=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )


@pytest.mark.parametrize(("status_code", "cancelled"), [(202, True), (409, False)])
async def test_github_actions_cancel_reports_whether_the_run_was_still_running(
    status_code: int, cancelled: bool
) -> None:
    result = await cancel_experiment(
        "12345",
        backend="github_actions",
        github_client=_github_client(status_code),
        github_owner="airas-org",
        repository_name="experiment-repo",
    )
    assert result == {
        "execution_id": "12345",
        "backend": "github_actions",
        "cancelled": cancelled,
        "status": None,
    }


class FakeSeyvalClient:
    def __init__(self, status_after_cancel: str) -> None:
        self.status_after_cancel = status_after_cancel
        self.cancelled: list[str] = []

    async def acancel_run(self, run_id: str) -> None:
        self.cancelled.append(run_id)

    async def aget_run(self, run_id: str) -> dict[str, Any]:
        return {"status": self.status_after_cancel}


@pytest.mark.parametrize(
    ("status", "cancelled"), [("cancelled", True), ("completed", False)]
)
async def test_seyval_cancel_rereads_the_run_for_its_status(
    status: str, cancelled: bool
) -> None:
    fake = FakeSeyvalClient(status)
    result = await cancel_experiment(
        "seyval-run-1", backend="seyval", seyval_client=cast(SeyvalClient, fake)
    )
    assert fake.cancelled == ["seyval-run-1"]
    assert result["status"] == status
    assert result["cancelled"] is cancelled


async def test_each_backend_needs_only_its_own_client() -> None:
    with pytest.raises(ValueError, match="seyval_client"):
        await cancel_experiment("r", backend="seyval")
    with pytest.raises(ValueError, match="github_client"):
        await cancel_experiment(
            "1", backend="github_actions", github_owner="o", repository_name="r"
        )
    with pytest.raises(ValueError, match="seyval_client"):
        await get_experiment_run_status("r", backend="seyval")
    with pytest.raises(ValueError, match="github_client"):
        await get_experiment_run_status(
            "1", backend="github_actions", github_owner="o", repository_name="r"
        )


async def test_github_actions_needs_the_repository() -> None:
    with pytest.raises(ValueError, match="github_owner and repository_name"):
        await cancel_experiment(
            "1", backend="github_actions", github_client=_github_client(202)
        )


async def test_the_mcp_tool_does_not_touch_github_credentials_for_seyval(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from airas.mcp.tools import execution as tools

    def no_github() -> GithubClient:
        raise RuntimeError("GH_PERSONAL_ACCESS_TOKEN is not configured")

    monkeypatch.setattr(tools, "_github_client", no_github)
    monkeypatch.setattr(
        tools,
        "_seyval_client",
        lambda: cast(SeyvalClient, FakeSeyvalClient("cancelled")),
    )
    result = await tools.cancel_experiment("seyval-run-1", backend="seyval")
    assert result["cancelled"] is True
