from logging import getLogger

logger = getLogger(__name__)


def check_workflow_completion(
    workflow_runs_response: dict | None,
    baseline_count: int,
) -> tuple[int | None, bool]:
    if not workflow_runs_response:
        return None, False

    workflow_runs = workflow_runs_response.get("workflow_runs", [])
    current_count = len(workflow_runs)

    logger.info(f"Current workflow count: {current_count}, baseline: {baseline_count}")

    # Check if there's a new workflow run
    if current_count > baseline_count and workflow_runs:
        latest_run = workflow_runs[0]  # Most recent run
        status = latest_run.get("status")
        conclusion = latest_run.get("conclusion")

        logger.debug(f"Workflow status: {status}, conclusion: {conclusion}")

        # Check if workflow is completed
        if status == "completed" and conclusion is not None:
            run_id = latest_run.get("id")
            logger.info(f"Workflow {run_id} completed with conclusion: {conclusion}")
            return run_id, True

    return None, False
