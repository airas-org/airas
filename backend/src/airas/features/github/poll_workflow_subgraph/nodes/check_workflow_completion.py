from logging import getLogger

logger = getLogger(__name__)


def check_workflow_completion(
    workflow_runs_response: dict | None,
    baseline_count: int,
    previous_count: int | None,
) -> tuple[int | None, bool, int]:
    if not workflow_runs_response:
        return None, False, baseline_count

    workflow_runs = workflow_runs_response.get("workflow_runs", [])
    current_count = len(workflow_runs)

    logger.info(
        f"Current workflow count: {current_count}, baseline: {baseline_count}, "
        f"previous: {previous_count}"
    )

    # Check if there are new workflows since baseline
    if current_count <= baseline_count:
        logger.info("No new workflows detected")
        return None, False, current_count

    # If previous_count is None, this is the first check - just record the count
    if previous_count is None:
        logger.info("First check - recording current count")
        return None, False, current_count

    # Check if count has stabilized (no new workflows started)
    if current_count == previous_count:
        latest_run = workflow_runs[0]  # Most recent run
        status = latest_run.get("status")
        conclusion = latest_run.get("conclusion")

        logger.info(
            f"Workflow count stable. Latest workflow status: {status}, "
            f"conclusion: {conclusion}"
        )

        if status == "completed" and conclusion is not None:
            run_id = latest_run.get("id")
            logger.info(
                f"Recursive workflow chain completed. Final workflow {run_id} "
                f"with conclusion: {conclusion}"
            )
            return run_id, True, current_count

    logger.info("Workflow chain still in progress")
    return None, False, current_count
