import time
from logging import getLogger

from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo

logger = getLogger(__name__)

_POLL_INTERVAL_SEC = 10
_TIMEOUT_SEC = 600


def prepare_images_for_html(
    github_repository: GitHubRepositoryInfo,
    experiment_branches: list[
        str
    ],  # TODO: Replace with the branch name selected by the AnalysisSubgraph.
    workflow_file: str = "prepare_images_for_html.yml",
    client: GithubClient | None = None,
) -> str | None:
    if client is None:
        client = GithubClient()

    github_owner = github_repository.github_owner
    repository_name = github_repository.repository_name
    branch_name = github_repository.branch_name or "main"

    try:
        workflow_runs_data = client.list_workflow_runs(
            github_owner=github_owner,
            repository_name=repository_name,
            branch_name=branch_name,
        )
        if workflow_runs_data is None:
            raise ValueError(
                f"Failed to get baseline workflow count for {github_owner}/{repository_name} on branch {branch_name}"
            )
        base_workflow_run_count = workflow_runs_data["total_count"]
        logger.info(f"Baseline workflow run count: {base_workflow_run_count}")

        success = client.create_workflow_dispatch(
            github_owner,
            repository_name,
            workflow_file,
            ref=branch_name,
            inputs={"selected_branches": ",".join(experiment_branches)},
        )
        if not success:
            raise ValueError(
                f"Failed to dispatch workflow {workflow_file} for {github_owner}/{repository_name} on branch {branch_name}"
            )

        logger.info(f"Workflow {workflow_file} dispatched successfully")

        start_time = time.time()
        new_workflow_run_id = None

        while True:
            time.sleep(_POLL_INTERVAL_SEC)

            if time.time() - start_time > _TIMEOUT_SEC:
                raise TimeoutError(
                    f"Workflow execution timed out after {_TIMEOUT_SEC} seconds"
                )

            response = client.list_workflow_runs(
                github_owner, repository_name, branch_name
            )
            if not response:
                raise ValueError(
                    f"Failed to retrieve workflow runs for {github_owner}/{repository_name} on branch {branch_name}"
                )

            current_workflow_run_count = response["total_count"]
            workflow_runs = response.get("workflow_runs", [])

            if (
                current_workflow_run_count <= base_workflow_run_count
                or not workflow_runs
            ):
                logger.debug(
                    f"Waiting for {workflow_file} completion... ({time.time() - start_time:.1f}s elapsed)"
                )
                continue

            latest_run = workflow_runs[0]

            if new_workflow_run_id is None:
                new_workflow_run_id = latest_run.get("id")
                logger.info(f"New workflow run detected: {new_workflow_run_id}")

            if latest_run.get("id") != new_workflow_run_id:
                logger.debug(
                    f"Waiting for {workflow_file} completion... ({time.time() - start_time:.1f}s elapsed)"
                )
                continue

            status = latest_run.get("status")
            conclusion = latest_run.get("conclusion")

            logger.info(
                f"Workflow {workflow_file} status: {status}, conclusion: {conclusion}"
            )

            if status != "completed":
                logger.debug(
                    f"Waiting for {workflow_file} completion... ({time.time() - start_time:.1f}s elapsed)"
                )
                continue

            if conclusion != "success":
                raise ValueError(
                    f"Workflow {workflow_file} completed with conclusion: {conclusion}"
                )

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
        logger.error(f"Failed to dispatch workflow: {e}")
        return None
