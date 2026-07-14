import os
from logging import getLogger

import wandb
from wandb.errors import CommError

from airas.infra.retry_policy import make_retry_policy

logger = getLogger(__name__)

WANDB_RETRY = make_retry_policy(
    max_retries=5,
    retryable_exc=(CommError, ConnectionError, TimeoutError),
)


class WandbClient:
    def __init__(self):
        api_key = os.environ["WANDB_API_KEY"]
        wandb.login(key=api_key)
        self.api = wandb.Api()

    @WANDB_RETRY
    def retrieve_run_metrics(self, entity: str, project: str, run_id: str):
        run = self.api.run(f"{entity}/{project}/{run_id}")
        metrics_dataframe = run.history()
        return metrics_dataframe


if __name__ == "__main__":
    client = WandbClient()
    entity = "toma_tanaka"
    project = "huggingface_deepspeed"
    run_id = "qqqqquyc"
    metrics_dataframe = client.retrieve_run_metrics(entity, project, run_id)
    print(metrics_dataframe)
