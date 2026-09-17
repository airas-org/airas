from typing import Any

from airas.core.types.github import GitHubConfig
from airas.mcp.app import mcp
from airas.mcp.context import _github_client
from airas.usecases.repository import prepare_repository as prepare_repository_usecase
from airas.usecases.repository import (
    set_github_actions_secrets as set_github_actions_secrets_usecase,
)


@mcp.tool()
async def prepare_repository(
    github_owner: str,
    repository_name: str,
    branch_name: str = "main",
    is_private: bool = False,
    protected_branch: str | None = None,
) -> dict[str, Any]:
    """Create a GitHub repository for running experiments, ready to enforce.

    Creates the repository from the AIRAS experiment template and the
    working branch, and returns `html_url` and `clone_url` so the next step,
    cloning it locally, needs nothing reconstructed by hand. Run it once
    before writing experiment code, then `set_github_actions_secrets`.

    It also protects `protected_branch` (the working branch unless another
    is named) and points GitHub Pages at the artifact the `Publish HTML`
    workflow deploys. Both are setup whose absence is invisible: without
    branch protection a red CI run can simply be pushed past, so they happen
    here rather than being left to a later call.

    Branch protection is what makes the record's guarantees enforceable
    instead of advisory: the record and paper gates become required status
    checks, admins included, with force pushes and deletions refused because
    the record's evidence is its git history. Squash and rebase merging are
    disabled repository-wide, since verification asks whether each run's
    recorded commit is an ancestor of HEAD and a rewrite breaks that. So
    work on a branch and, once the gate is green on a commit, fast-forward
    that same sha onto the protected branch. On GitHub's free plan branch
    protection is only available on public repositories, which is why
    `is_private` defaults to false.

    A step that fails does not abort the creation; it is reported in
    `warnings` and in its own flag. **A repository whose `branch_protected`
    is false is not enforcing anything**; say so rather than proceeding as
    though it were. The call is safe to repeat on a repository it created,
    and re-running it is how a failed CI setup gets repaired, e.g. once the
    token has admin rights.

    Requires GH_PERSONAL_ACCESS_TOKEN with admin rights on the repository.
    """
    return await prepare_repository_usecase.prepare_repository(
        GitHubConfig(
            github_owner=github_owner,
            repository_name=repository_name,
            branch_name=branch_name,
        ),
        github_client=_github_client(),
        is_private=is_private,
        protected_branch=protected_branch,
    )


@mcp.tool()
async def set_github_actions_secrets(
    github_owner: str,
    repository_name: str,
    branch_name: str = "main",
    secret_names: list[str] | None = None,
) -> dict[str, Any]:
    """Copy locally configured API keys into the repository's Actions secrets.

    Run once right after `prepare_repository`, and again when a key is
    added or rotated. The record gate needs `SEYVAL_API_KEY`
    in the repository to re-fetch each run's stored outputs and compare them
    against what the repository holds; without it that check is skipped
    rather than failed, so CI looks green without having run it.

    Reads the values from this machine's environment and writes them
    encrypted; no value appears in the result. `secret_names` defaults to
    every key airas knows about, and a name with no local value is skipped
    rather than failing. Requires GH_PERSONAL_ACCESS_TOKEN with admin rights
    on the repository.
    """
    secrets_set = await set_github_actions_secrets_usecase.set_github_actions_secrets(
        GitHubConfig(
            github_owner=github_owner,
            repository_name=repository_name,
            branch_name=branch_name,
        ),
        github_client=_github_client(),
        secret_names=secret_names,
    )
    return {"secrets_set": secrets_set}
