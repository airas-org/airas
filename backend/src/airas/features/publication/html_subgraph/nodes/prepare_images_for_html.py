from logging import getLogger

from airas.features.execution.execute_experiment_subgraph.workflow_executor import (
    WorkflowExecutor,
)
from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_session import ResearchSession

logger = getLogger(__name__)


async def prepare_images_for_html(
    github_repository: GitHubRepositoryInfo,
    research_session: ResearchSession,
    github_client: GithubClient,
    workflow_file: str = "prepare_images_for_html.yml",
) -> str | None:
    github_owner = github_repository.github_owner
    repository_name = github_repository.repository_name
    branch_name = github_repository.branch_name or "main"

    executor = WorkflowExecutor(github_client)

    if not (iteration := research_session.best_iteration):
        logger.error(
            "No best_iteration found in research_session. Cannot prepare images without iteration_id."
        )
        return None

    inputs: dict = {
        "iteration_id": str(iteration.iteration_id),
    }

    try:
        result = await executor.execute_workflow(
            github_owner=github_owner,
            repository_name=repository_name,
            branch_name=branch_name,
            workflow_file=workflow_file,
            inputs=inputs,
        )

        if not result.success:
            logger.error(f"Workflow failed: {result.error_message}")
            return None

        relative_path = f"branches/{branch_name}/index.html"
        github_pages_url = (
            f"https://{github_owner}.github.io/{repository_name}/{relative_path}"
        )
        logger.info(f"Workflow {workflow_file} completed successfully")
        logger.info(
            f"GitHub Pages build triggered. HTML will be available at: {github_pages_url} "
            "(It may take a few minutes to reflect on GitHub Pages)"
        )
        return github_pages_url

    except Exception as e:
        logger.error(f"Failed to execute workflow: {e}")
        return None
