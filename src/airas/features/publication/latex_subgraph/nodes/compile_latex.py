from logging import getLogger

from airas.features.execution.execute_experiment_subgraph.workflow_executor import (
    WorkflowExecutor,
)
from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo
from airas.types.latex import LATEX_TEMPLATE_NAME
from airas.types.research_session import ResearchSession

logger = getLogger(__name__)


async def compile_latex(
    github_repository_info: GitHubRepositoryInfo,
    research_session: ResearchSession,
    github_client: GithubClient,
    workflow_file: str = "compile_latex_with_open_code.yml",
    latex_template_name: LATEX_TEMPLATE_NAME = "iclr2024",
) -> bool:
    github_owner = github_repository_info.github_owner
    repository_name = github_repository_info.repository_name
    branch_name = github_repository_info.branch_name

    executor = WorkflowExecutor(github_client)

    if not (iteration := research_session.best_iteration):
        logger.error(
            "No best_iteration found in research_session. Cannot compile LaTeX without iteration_id."
        )
        return False

    workflow_inputs = {
        "subdir": latex_template_name,
        "iteration_id": str(iteration.iteration_id),
    }

    try:
        result = await executor.execute_workflow(
            github_owner=github_owner,
            repository_name=repository_name,
            branch_name=branch_name,
            workflow_file=workflow_file,
            inputs=workflow_inputs,
        )

        if result.success:
            logger.info(f"Workflow {workflow_file} completed successfully")
            return True
        else:
            logger.error(f"Workflow {workflow_file} failed: {result.error_message}")
            return False

    except Exception as e:
        logger.error(f"Failed to execute workflow: {e}")
        return False
