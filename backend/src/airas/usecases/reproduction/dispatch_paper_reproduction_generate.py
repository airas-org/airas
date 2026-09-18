from typing import Any

from airas.core.types.github import GitHubActionsAgent, GitHubConfig
from airas.infra.github_client import GithubClient
from airas.usecases.reproduction.nodes.dispatch_reproduction_workflow import (
    dispatch_reproduction_workflow,
)
from airas.usecases.reproduction.nodes.generate_repro_id import generate_repro_id

WORKFLOW_FILE = "run_paper_reproduction_generate.yml"


async def dispatch_paper_reproduction_generate(
    github_client: GithubClient,
    github_config: GitHubConfig,
    paper_url: str,
    instruction: str,
    model: str,
    *,
    repo_url: str = "",
    github_actions_agent: GitHubActionsAgent = "claude_code",
    runner_label: list[str] | None = None,
    workflow_file: str = WORKFLOW_FILE,
) -> dict[str, Any]:
    repro_id = generate_repro_id(paper_url)
    dispatched = await dispatch_reproduction_workflow(
        github_client,
        github_config,
        workflow_file,
        {
            "repro_id": repro_id,
            "paper_url": paper_url,
            "repo_url": repo_url,
            "instruction": instruction,
            "github_actions_agent": github_actions_agent,
            "model_name": model,
        },
        runner_label,
    )
    return {"dispatched": dispatched, "repro_id": repro_id}
