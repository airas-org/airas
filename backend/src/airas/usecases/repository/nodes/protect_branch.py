from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient

RECORD_GATE_CHECK_NAME = "Verify the record"
# Values only, no PDF build: the build commits back onto the protected branch,
# so requiring it would deadlock.
PAPER_GATE_CHECK_NAME = "Verify the paper"
REQUIRED_CHECK_NAMES = [RECORD_GATE_CHECK_NAME, PAPER_GATE_CHECK_NAME]


async def protect_branch(
    github_config: GitHubConfig,
    branch_name: str,
    *,
    github_client: GithubClient,
) -> tuple[bool, bool]:
    protected = await github_client.aupdate_branch_protection(
        github_owner=github_config.github_owner,
        repository_name=github_config.repository_name,
        branch_name=branch_name,
        required_check_names=REQUIRED_CHECK_NAMES,
        enforce_admins=True,
    )
    # Squash and rebase rewrite commits; verification asks whether each run's
    # recorded commit is an ancestor of HEAD.
    merge_settings = await github_client.aupdate_repository_merge_settings(
        github_owner=github_config.github_owner,
        repository_name=github_config.repository_name,
    )
    return protected, merge_settings
