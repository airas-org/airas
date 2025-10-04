import json
import time
from logging import getLogger

from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo
from airas.types.latex import LATEX_TEMPLATE_NAME

logger = getLogger(__name__)

_POLL_INTERVAL_SEC = 10
_TIMEOUT_SEC = 600


def execute_workflow(
    github_repository: GitHubRepositoryInfo,
    workflow_file_name: str,
    latex_template_name: LATEX_TEMPLATE_NAME = "iclr2024",
    experiment_branches: list[str]
    | None = None,  # TODO: Replace with the branch name selected by the AnalysisSubgraph.
    client: GithubClient | None = None,
) -> bool:
    """
    Execute a GitHub Actions workflow and wait for completion.

    Args:
        github_repository: GitHub repository information
        workflow_file_name: Name of the workflow YAML file (e.g., "compile_latex.yml", "run_chktex.yml")
        latex_template_name: LaTeX template name to pass as input
        client: Optional GitHub client instance

    Returns:
        True if workflow completed successfully, False otherwise
    """
    client = client or GithubClient()
    github_owner = github_repository.github_owner
    repository_name = github_repository.repository_name
    branch_name = github_repository.branch_name

    # ベースラインのワークフロー実行数を取得
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

    # ワークフローを実行
    workflow_inputs = {
        "subdir": latex_template_name,
    }
    if experiment_branches:
        workflow_inputs["selected_branches"] = json.dumps(experiment_branches)

    success = client.create_workflow_dispatch(
        github_owner=github_owner,
        repository_name=repository_name,
        workflow_file_name=workflow_file_name,
        ref=branch_name,
        inputs=workflow_inputs,
    )
    if not success:
        raise ValueError(
            f"Failed to dispatch workflow {workflow_file_name} for {github_owner}/{repository_name} on branch {branch_name}"
        )

    logger.info(f"Workflow {workflow_file_name} dispatched successfully")

    # Wait for GitHub to propagate file changes before workflow starts
    logger.info("Waiting for GitHub file propagation...")
    time.sleep(5)

    # ワークフローの完了を待機
    start_time = time.time()
    new_workflow_run_id = None

    while True:
        time.sleep(_POLL_INTERVAL_SEC)

        # タイムアウトチェック
        if time.time() - start_time > _TIMEOUT_SEC:
            raise TimeoutError(
                f"Workflow execution timed out after {_TIMEOUT_SEC} seconds"
            )

        response = client.list_workflow_runs(github_owner, repository_name, branch_name)
        if not response:
            raise ValueError(
                f"Failed to retrieve workflow runs for {github_owner}/{repository_name} on branch {branch_name}"
            )

        current_workflow_run_count = response["total_count"]
        workflow_runs = response.get("workflow_runs", [])

        # 新しいワークフローが開始されたかチェック
        if current_workflow_run_count > base_workflow_run_count and workflow_runs:
            latest_run = workflow_runs[0]

            # 新しいワークフローIDを記録（初回のみ）
            if new_workflow_run_id is None:
                new_workflow_run_id = latest_run.get("id")
                logger.info(f"New workflow run detected: {new_workflow_run_id}")

            # 対象のワークフローの状態をチェック
            if latest_run.get("id") == new_workflow_run_id:
                status = latest_run.get("status")
                conclusion = latest_run.get("conclusion")

                logger.info(
                    f"Workflow {workflow_file_name} status: {status}, conclusion: {conclusion}"
                )

                if status == "completed":
                    if conclusion == "success":
                        logger.info(
                            f"Workflow {workflow_file_name} completed successfully"
                        )
                        return True
                    else:
                        raise ValueError(
                            f"Workflow {workflow_file_name} completed with conclusion: {conclusion}"
                        )

        logger.debug(
            f"Waiting for {workflow_file_name} completion... ({time.time() - start_time:.1f}s elapsed)"
        )
        continue


if __name__ == "__main__":
    github_repository = GitHubRepositoryInfo(
        github_owner="auto-res2",
        repository_name="tanaka-20250803-v3",
        branch_name="main",
    )

    # Test LaTeX compilation workflow
    result = execute_workflow(
        github_repository=github_repository,
        workflow_file_name="compile_latex.yml",
        latex_template_name="iclr2024",
    )
    print(f"LaTeX compilation result: {result}")

    # Test chktex workflow
    result = execute_workflow(
        github_repository=github_repository,
        workflow_file_name="run_chktex.yml",
        latex_template_name="iclr2024",
    )
    print(f"chktex execution result: {result}")
