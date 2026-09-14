import json
from typing import Any, cast

import httpx
import pytest

from airas.core.types.experiment_history import RunStage
from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient
from airas.infra.seyval_client import SeyvalClient, parse_overrides
from airas.usecases.executors.dispatch_experiment_subgraph.dispatch_experiment_subgraph import (
    RUN_COMMAND_TEMPLATE,
    DispatchExperimentSubgraph,
)

GITHUB_CONFIG = GitHubConfig(
    github_owner="airas-org", repository_name="experiment-repo", branch_name="main"
)


def _seyval(**kwargs) -> DispatchExperimentSubgraph:
    return DispatchExperimentSubgraph(
        backend="seyval",
        github_client=cast(GithubClient, object()),
        seyval_client=cast(SeyvalClient, object()),
        **kwargs,
    )


def test_seyval_needs_its_client():
    with pytest.raises(ValueError, match="seyval_client"):
        DispatchExperimentSubgraph(
            backend="seyval", github_client=cast(GithubClient, object())
        )


def test_the_default_command_is_the_repository_entry_point_and_carries_its_overrides():
    command = RUN_COMMAND_TEMPLATE.format(run_id="run-1", mode="full")
    assert command == "make run RUN_ID=run-1 MODE=full"
    # The provenance manifest is realized from the recorded argv, with the
    # Makefile's upper-case variables as the record's lower-case params.
    assert parse_overrides(["bash", "-c", command]) == {
        "run_id": "run-1",
        "mode": "full",
    }


async def test_github_actions_dispatch_returns_the_created_run_id() -> None:
    bodies: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith(
            "/actions/workflows/run_experiment.yml/dispatches"
        )
        bodies.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "workflow_run_id": 12345,
                "run_url": "https://api.github.com/repos/airas-org/experiment-repo/actions/runs/12345",
                "html_url": "https://github.com/airas-org/experiment-repo/actions/runs/12345",
            },
        )

    client = GithubClient(
        github_token="t",
        async_session=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    result = await (
        DispatchExperimentSubgraph(
            backend="github_actions", github_client=client, run_stage=RunStage.SANITY
        )
        .build_graph()
        .ainvoke({"github_config": GITHUB_CONFIG, "run_id": "run-1"})
    )

    assert result["dispatched"] is True
    assert result["execution_id"] == "12345"
    assert result["execution_url"].endswith("/actions/runs/12345")
    assert bodies[0]["return_run_details"] is True
    assert bodies[0]["inputs"]["mode"] == "sanity"


class FakeSeyvalClient:
    def __init__(self, analysis: dict[str, Any]) -> None:
        self.analysis = analysis
        self.started: list[dict[str, Any]] = []

    async def aregister_repository(self, git_url: str, workspace_id: str | None = None):
        return {"id": "repo-1"}

    async def apull_repository(self, repository_id: str):
        return {"branches": [{"name": "main", "commit_hash": "c" * 40}]}

    async def aget_analysis(self, repository_id: str, commit_hash: str):
        return self.analysis

    async def astart_run(
        self, repository_id, commit_hash, experiment_id, analysis_id, **kw
    ):
        self.started.append(
            {"experiment_id": experiment_id, "analysis_id": analysis_id, **kw}
        )
        return {"run_id": "seyval-run-1", "run_url": "https://seyval.test/runs/1"}


async def _dispatch_seyval(analysis: dict[str, Any]) -> tuple[dict, FakeSeyvalClient]:
    fake = FakeSeyvalClient(analysis)
    result = await (
        DispatchExperimentSubgraph(
            backend="seyval",
            github_client=cast(GithubClient, object()),
            seyval_client=cast(SeyvalClient, fake),
            run_stage=RunStage.SANITY,
            compute_id="byo:abc",
            resource_count=1,
        )
        .build_graph()
        .ainvoke({"github_config": GITHUB_CONFIG, "run_id": "run-1"})
    )
    return result, fake


async def test_seyval_dispatch_starts_the_analyzed_experiment_with_the_chain() -> None:
    result, fake = await _dispatch_seyval(
        {
            "status": "completed",
            "analysis_id": "an-1",
            "experiments": [{"id": "exp_a"}, {"id": "exp_b"}],
            "primary_ids": ["exp_b"],
        }
    )
    assert result["execution_id"] == "seyval-run-1"
    started = fake.started[0]
    assert (started["experiment_id"], started["analysis_id"]) == ("exp_b", "an-1")
    assert started["user_dockerfile_path"] == "Dockerfile"
    assert started["command_args"][:2] == ["bash", "-c"]
    assert started["command_args"][2] == "make run RUN_ID=run-1 MODE=sanity"


async def test_seyval_dispatch_asks_for_a_retry_while_the_analysis_runs() -> None:
    with pytest.raises(ValueError, match="still analyzing"):
        await _dispatch_seyval({"status": "running", "analysis_id": "an-1"})
