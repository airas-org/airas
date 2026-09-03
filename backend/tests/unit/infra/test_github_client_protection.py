"""Branch protection and merge settings, asserted on the wire.

What these calls *send* is the whole point: a protection payload that
omits `enforce_admins`, or leaves squash merging enabled, still returns
200 and still looks configured — while protecting nothing that matters.
So the request bodies are captured and checked, not just the return value.
"""

import json

import httpx
import pytest

from airas.infra.github_client import GithubClient, GithubClientFatalError

OWNER = "airas-org"
REPO = "experiment-repo"
BRANCH = "main"
CHECK = "Verify the record"


class RequestLog:
    def __init__(self) -> None:
        self.protection: list[dict] = []
        self.repo_settings: list[dict] = []


def _client(log: RequestLog, status: int = 200) -> GithubClient:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        body = json.loads(request.content) if request.content else {}

        if request.method == "PUT" and path.endswith("/protection"):
            log.protection.append(body)
            return httpx.Response(status, json={"url": path})
        if request.method == "PATCH" and path == f"/repos/{OWNER}/{REPO}":
            log.repo_settings.append(body)
            return httpx.Response(status, json={"full_name": f"{OWNER}/{REPO}"})

        raise AssertionError(f"Unexpected request: {request.method} {path}")

    return GithubClient(
        github_token="test-token",
        async_session=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )


@pytest.fixture
def log() -> RequestLog:
    return RequestLog()


# ------------------------------------------------------------- protection


async def test_protection_requires_the_named_check(log: RequestLog) -> None:
    assert await _client(log).aupdate_branch_protection(
        github_owner=OWNER,
        repository_name=REPO,
        branch_name=BRANCH,
        required_check_names=[CHECK],
    )

    (sent,) = log.protection
    assert sent["required_status_checks"]["contexts"] == [CHECK]
    # The branch must be current with the base, so the checks that passed
    # ran against this tree rather than an older one.
    assert sent["required_status_checks"]["strict"] is True


async def test_protection_applies_to_admins(log: RequestLog) -> None:
    """Without this the rule exempts exactly the person who set it."""
    await _client(log).aupdate_branch_protection(
        github_owner=OWNER,
        repository_name=REPO,
        branch_name=BRANCH,
        required_check_names=[CHECK],
    )
    assert log.protection[0]["enforce_admins"] is True


async def test_protection_forbids_rewriting_the_history(log: RequestLog) -> None:
    """The record's evidence is its git history.

    A force push does not fail verification — it removes what verification
    reads, which is worse, because the result is a repository that passes.
    """
    await _client(log).aupdate_branch_protection(
        github_owner=OWNER,
        repository_name=REPO,
        branch_name=BRANCH,
        required_check_names=[CHECK],
    )
    sent = log.protection[0]
    assert sent["allow_force_pushes"] is False
    assert sent["allow_deletions"] is False


async def test_protection_does_not_require_a_pull_request(log: RequestLog) -> None:
    """A green check on the commit is the gate, not a human's approval.

    Requiring a PR would also close off fast-forwarding the very sha CI
    judged onto the protected branch.
    """
    await _client(log).aupdate_branch_protection(
        github_owner=OWNER,
        repository_name=REPO,
        branch_name=BRANCH,
        required_check_names=[CHECK],
    )
    sent = log.protection[0]
    # Present-and-null, not absent: the endpoint requires every top-level key.
    assert "required_pull_request_reviews" in sent
    assert sent["required_pull_request_reviews"] is None


async def test_protection_without_admin_rights_is_fatal(log: RequestLog) -> None:
    with pytest.raises(GithubClientFatalError, match="admin"):
        await _client(log, status=403).aupdate_branch_protection(
            github_owner=OWNER,
            repository_name=REPO,
            branch_name=BRANCH,
            required_check_names=[CHECK],
        )


# ---------------------------------------------------------- merge settings


async def test_squash_and_rebase_are_disabled(log: RequestLog) -> None:
    """Both rewrite commits.

    Verification asks whether each run's recorded commit is an ancestor of
    HEAD; after a rewrite it is not, so the merge that was meant to publish
    a result is what invalidates it. A merge commit keeps the originals in
    the ancestry, so it stays available.
    """
    assert await _client(log).aupdate_repository_merge_settings(
        github_owner=OWNER, repository_name=REPO
    )

    (sent,) = log.repo_settings
    assert sent["allow_squash_merge"] is False
    assert sent["allow_rebase_merge"] is False
    assert sent["allow_merge_commit"] is True
