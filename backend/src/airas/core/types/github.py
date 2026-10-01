from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class GitHubConfig(BaseModel):
    github_owner: str = Field(..., description="GitHub owner of the repository")
    repository_name: str = Field(..., description="Name of the repository")
    branch_name: str = Field(..., description="Branch name")


GitHubRepositoryInfo = GitHubConfig


def require_github_repo(
    github_owner: str | None, repository_name: str | None
) -> tuple[str, str]:
    if not github_owner or not repository_name:
        raise ValueError(
            "github_owner and repository_name are required for the "
            "github_actions backend"
        )
    return github_owner, repository_name


# See: https://docs.github.com/ja/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/about-status-checks#check-statuses-and-conclusions
class GitHubActionsStatus(str, Enum):
    COMPLETED = "completed"
    EXPECTED = "expected"
    FAILURE = "failure"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"
    QUEUED = "queued"
    REQUESTED = "requested"
    STARTUP_FAILURE = "startup_failure"
    WAITING = "waiting"


class GitHubActionsConclusion(str, Enum):
    ACTION_REQUIRED = "action_required"
    CANCELLED = "cancelled"
    FAILURE = "failure"
    NEUTRAL = "neutral"
    SKIPPED = "skipped"
    STALE = "stale"
    SUCCESS = "success"
    TIMED_OUT = "timed_out"


GitHubActionsAgent = Literal["claude_code", "open_code"]
