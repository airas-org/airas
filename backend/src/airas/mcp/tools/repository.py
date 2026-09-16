"""Experiment repository setup on GitHub."""

from typing import Any

from airas.core.types.github import GitHubConfig
from airas.mcp.app import mcp
from airas.mcp.context import (
    _github_client,
)
from airas.usecases.repository.prepare_repository_subgraph.prepare_repository_subgraph import (
    PrepareRepositorySubgraph,
)
from airas.usecases.repository.set_github_actions_secrets_subgraph import (
    SetGithubActionsSecretsSubgraph,
)


@mcp.tool()
async def prepare_repository(
    github_owner: str,
    repository_name: str,
    branch_name: str = "main",
    is_private: bool = False,
    protected_branch: str = "main",
    configure_ci: bool = True,
) -> dict[str, Any]:
    """Create a GitHub repository for running experiments, ready to enforce.

    Sets up the repository (from the AIRAS experiment template) and the
    working branch. Run this once before `dispatch_code_generation`.
    Returns `html_url` and `clone_url` alongside the readiness flags, so the
    next step — cloning it locally — needs nothing reconstructed by hand.

    `configure_ci` also provisions the Actions secrets, protects
    `protected_branch` and points GitHub Pages at the artifact the
    `Publish HTML` workflow deploys (so no gh-pages branch is needed),
    because all three are the kind of setup whose absence is
    invisible: without `SEYVAL_API_KEY` the provenance cross-check degrades
    to a skip rather than a failure, and without branch protection every
    guarantee in the record rests on the agent choosing to respect a red
    CI run. A step that has to be remembered to be safe is a step that will
    eventually be forgotten, so it happens here rather than being left to a
    later call. Pass `configure_ci=False` only when the token lacks admin
    rights and you intend to configure the repository some other way.

    Neither failure aborts the creation — the repository exists either way,
    and losing that result would help nobody — but each is reported in
    `warnings` and in its own flag. **A repository whose `branch_protected`
    is false is not enforcing anything**; say so rather than proceeding as
    though it were.

    Requires GH_PERSONAL_ACCESS_TOKEN, with admin rights for `configure_ci`.
    """
    config = GitHubConfig(
        github_owner=github_owner,
        repository_name=repository_name,
        branch_name=branch_name,
    )
    result = (
        await PrepareRepositorySubgraph(
            github_client=_github_client(),
            is_github_repo_private=is_private,
        )
        .build_graph()
        .ainvoke({"github_config": config})
    )

    warnings: list[str] = []
    secrets_set = False
    branch_protected = False
    merge_settings_updated = False
    pages_enabled = False
    if configure_ci:
        try:
            secrets_set = await _apply_secrets(
                github_owner, repository_name, branch_name
            )
        except Exception as e:
            warnings.append(
                f"Actions secrets were not set ({e}). The provenance "
                "cross-check will be skipped rather than fail, so CI will "
                "look green without ever having run it — fix this before "
                "dispatching experiments (set_github_actions_secrets)."
            )
        try:
            branch_protected, merge_settings_updated = await _apply_branch_protection(
                github_owner,
                repository_name,
                protected_branch,
                [RECORD_GATE_CHECK_NAME, PAPER_GATE_CHECK_NAME],
            )
        except Exception as e:
            warnings.append(
                f"'{protected_branch}' was not protected ({e}). Nothing "
                "prevents a red or unchecked commit from landing on it, so "
                "the record's guarantees are advisory in this repository "
                "until it is fixed (protect_branch)."
            )
        try:
            pages_enabled = await _apply_pages(github_owner, repository_name)
        except Exception as e:
            warnings.append(
                f"GitHub Pages was not pointed at Actions ({e}); the Publish "
                "HTML workflow will have nowhere to deploy until the "
                "repository's Pages source is set to GitHub Actions."
            )

    return {
        "is_repository_ready": result["is_repository_ready"],
        "is_branch_ready": result["is_branch_ready"],
        "html_url": result["html_url"],
        "clone_url": result["clone_url"],
        "secrets_set": secrets_set,
        "branch_protected": branch_protected,
        "merge_settings_updated": merge_settings_updated,
        "pages_enabled": pages_enabled,
        "protected_branch": protected_branch if branch_protected else None,
        "warnings": warnings,
    }


@mcp.tool()
async def set_github_actions_secrets(
    github_owner: str,
    repository_name: str,
    branch_name: str = "main",
    secret_names: list[str] | None = None,
) -> dict[str, Any]:
    """Copy locally configured API keys into the repository's Actions secrets.

    Run this once, right after `prepare_repository`. CI is the only place a
    paper is judged, and the gate re-fetches each run's stored outputs from
    the compute platform to byte-compare them against what the repository
    holds. Without `SEYVAL_API_KEY` present in the repository that
    comparison cannot run, so the strongest check in the system degrades to
    a skip on any repository nobody remembered to provision — and it
    degrades quietly, which is why this is a setup step rather than
    something to reach for once CI complains.

    Reads the values from this machine's environment and writes them
    encrypted; no value appears in the result. `secret_names` defaults to
    every key airas knows about, and a name with no local value is skipped
    rather than failing. Requires GH_PERSONAL_ACCESS_TOKEN with admin rights
    on the repository.
    """
    return {
        "secrets_set": await _apply_secrets(
            github_owner, repository_name, branch_name, secret_names
        )
    }


RECORD_GATE_CHECK_NAME = "Verify the record"
# Values only, no PDF build: the build commits back onto the protected branch,
# so requiring it would deadlock. It stays in the non-required publish workflow.
PAPER_GATE_CHECK_NAME = "Verify the paper"


async def _apply_secrets(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    secret_names: list[str] | None = None,
) -> bool:
    config = GitHubConfig(
        github_owner=github_owner,
        repository_name=repository_name,
        branch_name=branch_name,
    )
    result = (
        await SetGithubActionsSecretsSubgraph(
            github_client=_github_client(),
            secret_names=secret_names,
        )
        .build_graph()
        .ainvoke({"github_config": config})
    )
    return bool(result["secrets_set"])


async def _apply_pages(github_owner: str, repository_name: str) -> bool:
    return await _github_client().aenable_pages_from_actions(
        github_owner, repository_name
    )


async def _apply_branch_protection(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    required_check_names: list[str],
) -> tuple[bool, bool]:
    client = _github_client()
    protected = await client.aupdate_branch_protection(
        github_owner=github_owner,
        repository_name=repository_name,
        branch_name=branch_name,
        required_check_names=required_check_names,
        enforce_admins=True,
    )
    merge_settings = await client.aupdate_repository_merge_settings(
        github_owner=github_owner,
        repository_name=repository_name,
    )
    return protected, merge_settings


@mcp.tool()
async def protect_branch(
    github_owner: str,
    repository_name: str,
    branch_name: str = "main",
    required_check_names: list[str] | None = None,
) -> dict[str, Any]:
    """Make the record's guarantees enforceable instead of advisory.

    Run this once, after `set_github_actions_secrets`. Everything else in
    the system derives its authority from this call: a local check can be
    ignored and a red CI run can be pushed past, so until the branch is
    protected the record's integrity rests on the agent choosing to respect
    it. Afterwards it rests on GitHub refusing the push.

    Sets three things on `branch_name`:

    - the record and paper gates as **required status checks** — always;
      `required_check_names` can add checks, never drop these — so a commit
      whose check is missing or red cannot land, by push or by merge;
    - `enforce_admins`, because the default exempts exactly the person who
      configured the rule — usually the repository's own owner, and so the
      one whose work most needs to be held to it;
    - no force pushes and no deletions, because the record's evidence *is*
      its git history: a rewrite does not fail verification, it removes
      what verification reads.

    It also disables squash and rebase merging repository-wide. Both rewrite
    commits, and verification asks whether each run's recorded commit is an
    ancestor of HEAD — after a rewrite it is not, so every claim in the
    repository silently becomes unverified at the moment of the merge. A
    merge commit keeps the original commits in the ancestry; a
    fast-forward push of the already-checked commit keeps the very sha CI
    judged.

    Requires GH_PERSONAL_ACCESS_TOKEN with admin rights on the repository.
    """
    contexts = list(
        dict.fromkeys(
            (required_check_names or [])
            + [RECORD_GATE_CHECK_NAME, PAPER_GATE_CHECK_NAME]
        )
    )
    protected, merge_settings = await _apply_branch_protection(
        github_owner, repository_name, branch_name, contexts
    )
    return {
        "branch_protected": protected,
        "merge_settings_updated": merge_settings,
        "branch": branch_name,
        "required_checks": contexts,
        "usage": (
            "work on a branch; when the record gate is green on that commit, "
            "fast-forward it onto the protected branch — the sha CI judged "
            "is then the sha that landed"
        ),
    }
