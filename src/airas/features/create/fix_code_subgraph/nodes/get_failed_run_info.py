import logging
from typing import Optional

from airas.services.api_client.github_client import GithubClient

logger = logging.getLogger(__name__)


def get_failed_run_info(
    github_repository: dict[str, str],
    github_client: GithubClient | None = None,
) -> Optional[dict]:
    """Get the most recent failed workflow run information"""
    github_client = github_client or GithubClient()

    try:
        # Get failed workflow runs for the branch
        runs_response = github_client.list_workflow_runs(
            github_owner=github_repository["github_owner"],
            repository_name=github_repository["repository_name"],
            branch_name=github_repository["branch_name"],
            status="failure",
            per_page=10,
        )

        if not runs_response or not runs_response.get("workflow_runs"):
            logger.warning(
                f"No failed workflow runs found for {github_repository['repository_name']}:{github_repository['branch_name']}"
            )
            return None

        # Get the most recent failed run
        failed_run = runs_response["workflow_runs"][0]
        run_id = failed_run["id"]

        logger.info(f"Found failed run: {run_id}")

        # Get jobs for this run
        jobs_response = github_client.list_workflow_run_jobs(
            github_owner=github_repository["github_owner"],
            repository_name=github_repository["repository_name"],
            run_id=run_id,
        )

        return {
            "run_id": run_id,
            "run_info": failed_run,
            "jobs": jobs_response.get("jobs", []) if jobs_response else [],
        }

    except Exception as e:
        logger.error(f"Error getting failed run info: {e}")
        return None


if __name__ == "__main__":
    # Test the function
    result = get_failed_run_info(
        github_repository="test-owner/test-repo",
        branch_name="develop",
    )
    print(f"Failed run info: {result}")
