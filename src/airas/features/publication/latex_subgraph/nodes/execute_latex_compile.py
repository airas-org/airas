import time
from logging import getLogger

from airas.services.api_client.github_client import GithubClient
from airas.types.latex import LATEX_TEMPLATE_NAME

logger = getLogger(__name__)

_POLL_INTERVAL_SEC = 10
_TIMEOUT_SEC = 600


def execute_latex_compile(
    github_repository: dict[str, str],
    latex_template_name: LATEX_TEMPLATE_NAME = "iclr2024",
) -> bool:
    LATEX_COMPILED_WORKFLOW_FILE = "compile_latex.yml"
    client = GithubClient()
    github_owner = github_repository["github_owner"]
    repository_name = github_repository["repository_name"]
    branch_name = github_repository["branch_name"]

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
    success = client.create_workflow_dispatch(
        github_owner=github_owner,
        repository_name=repository_name,
        workflow_file_name=LATEX_COMPILED_WORKFLOW_FILE,
        ref=branch_name,
        inputs={"subdir": latex_template_name},
    )
    if not success:
        raise ValueError(
            f"Failed to dispatch workflow {LATEX_COMPILED_WORKFLOW_FILE} for {github_owner}/{repository_name} on branch {branch_name}"
        )

    logger.info(f"Workflow {LATEX_COMPILED_WORKFLOW_FILE} dispatched successfully")

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

                logger.info(f"Workflow status: {status}, conclusion: {conclusion}")

                if status == "completed":
                    if conclusion == "success":
                        logger.info("Workflow completed successfully")
                        return True
                    else:
                        raise ValueError(
                            f"Workflow completed with conclusion: {conclusion}"
                        )

        logger.debug(
            f"Waiting for workflow completion... ({time.time() - start_time:.1f}s elapsed)"
        )
        continue


if __name__ == "__main__":
    github_repository = {
        "github_owner": "auto-res2",
        "repository_name": "tanaka-20250803-v3",
        "branch_name": "main",
    }
    result = execute_latex_compile(
        github_repository=github_repository,
        latex_template_name="iclr2024",
    )
