from logging import getLogger

logger = getLogger(__name__)


def get_latest_workflow_status(
    workflow_runs_response: dict | None,
) -> tuple[int | None, str | None, str | None]:
    if not workflow_runs_response:
        logger.info("No workflow runs response")
        return None, None, None

    workflow_runs = workflow_runs_response.get("workflow_runs", [])
    if not workflow_runs:
        logger.info("No workflow runs found")
        return None, None, None

    latest_run = workflow_runs[0]
    workflow_run_id = latest_run.get("id")
    status = latest_run.get("status")
    conclusion = latest_run.get("conclusion")

    logger.info(
        f"Latest workflow {workflow_run_id}: status={status}, conclusion={conclusion}"
    )

    return workflow_run_id, status, conclusion
