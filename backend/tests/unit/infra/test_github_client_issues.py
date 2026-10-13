"""Open issues are listed across every page, so a title already open is found
however many issues the repository has."""

import json

import httpx

from airas.infra.github_client import GithubClient

OWNER = "airas-org"
REPO = "experiment-repo"


def _client(handler) -> GithubClient:
    transport = httpx.MockTransport(handler)
    return GithubClient(
        github_token="test-token",
        sync_session=httpx.Client(transport=transport),
        async_session=httpx.AsyncClient(transport=transport),
    )


async def test_open_issue_titles_are_read_past_the_first_page() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params["page"])
        if page == 1:
            issues = [{"title": f"issue {n}"} for n in range(100)]
            issues[0]["pull_request"] = {"url": "..."}  # listed as an issue too
        else:
            issues = [{"title": "issue 100"}]
        return httpx.Response(200, json=issues)

    titles = await _client(handler).alist_open_issue_titles(OWNER, REPO)
    assert len(titles) == 100 and "issue 0" not in titles and "issue 100" in titles


async def test_an_issue_is_created_and_its_url_returned() -> None:
    sent: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(json.loads(request.content))
        return httpx.Response(
            201, json={"html_url": f"https://github.com/{OWNER}/{REPO}/issues/7"}
        )

    url = await _client(handler).acreate_issue(OWNER, REPO, "verifiable: x", "body")
    assert url.endswith("/issues/7") and sent == [
        {"title": "verifiable: x", "body": "body"}
    ]
