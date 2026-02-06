from logging import getLogger

from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient

logger = getLogger(__name__)


async def log_workflow_failure_details(
    workflow_run_id: int,
    github_config: GitHubConfig,
    github_client: GithubClient,
) -> None:
    try:
        jobs_response = await github_client.alist_workflow_run_jobs(
            github_owner=github_config.github_owner,
            repository_name=github_config.repository_name,
            run_id=workflow_run_id,
        )

        if not jobs_response or "jobs" not in jobs_response:
            logger.warning(
                f"Could not retrieve job details for workflow run {workflow_run_id}"
            )
            return

        jobs = jobs_response["jobs"]
        failed_jobs = [
            job
            for job in jobs
            if job.get("conclusion") in ["failure", "cancelled", "timed_out"]
        ]

        if failed_jobs:
            logger.error(f"=== Workflow {workflow_run_id} Failure Details ===")
            for job in failed_jobs:
                job_name = job.get("name", "Unknown")
                job_conclusion = job.get("conclusion", "Unknown")
                job_url = job.get("html_url", "N/A")

                logger.error(f"Failed Job: '{job_name}' - Conclusion: {job_conclusion}")
                logger.error(f"  Job URL: {job_url}")

                # Log failed steps if available
                steps = job.get("steps", [])
                failed_steps = [
                    step
                    for step in steps
                    if step.get("conclusion") in ["failure", "cancelled", "timed_out"]
                ]

                if failed_steps:
                    logger.error("Failed Steps:")
                    for step in failed_steps:
                        step_name = step.get("name", "Unknown")
                        step_conclusion = step.get("conclusion", "Unknown")
                        step_number = step.get("number", "?")
                        logger.error(
                            f"    [{step_number}] {step_name} - {step_conclusion}"
                        )

    except Exception as e:
        logger.warning(f"Error retrieving workflow failure details: {e}", exc_info=True)
