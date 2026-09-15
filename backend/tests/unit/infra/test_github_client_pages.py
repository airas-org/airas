"""Repository generation and GitHub Pages, asserted on the wire."""

import json

import httpx
import pytest

from airas.infra.github_client import GithubClient, GithubClientFatalError

OWNER = "airas-org"
REPO = "experiment-repo"


def _client(handler) -> GithubClient:
    transport = httpx.MockTransport(handler)
    return GithubClient(
        github_token="test-token",
        sync_session=httpx.Client(transport=transport),
        async_session=httpx.AsyncClient(transport=transport),
    )


def test_a_repository_is_generated_from_the_default_branch_only() -> None:
    sent: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/generate")
        sent.append(json.loads(request.content))
        return httpx.Response(201, json={"full_name": f"{OWNER}/{REPO}"})

    _client(handler).create_repository_from_template(
        github_owner=OWNER,
        repository_name=REPO,
        template_owner="airas-org",
        template_repo="airas-template",
    )
    assert sent[0]["include_all_branches"] is False


async def test_pages_are_served_from_actions_and_repointed_when_the_site_exists() -> (
    None
):
    calls: list[tuple[str, dict]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == f"/repos/{OWNER}/{REPO}/pages"
        calls.append((request.method, json.loads(request.content)))
        if request.method == "POST":
            return httpx.Response(409, json={"message": "Pages already enabled"})
        return httpx.Response(204)

    assert await _client(handler).aenable_pages_from_actions(OWNER, REPO) is True
    assert calls == [
        ("POST", {"build_type": "workflow"}),
        ("PUT", {"build_type": "workflow"}),
    ]


async def test_a_plan_without_pages_is_reported_in_githubs_words() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            json={
                "message": "Upgrade to GitHub Pro or make this repository public to enable this feature."
            },
        )

    with pytest.raises(GithubClientFatalError, match="make this repository public"):
        await _client(handler).aenable_pages_from_actions(OWNER, REPO)
