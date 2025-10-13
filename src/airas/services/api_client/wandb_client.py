import os

import wandb


class WandbClient:
    def __init__(self):
        api_key = os.environ["WANDB_API_KEY"]
        wandb.login(key=api_key)
        self.api = wandb.Api()

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
