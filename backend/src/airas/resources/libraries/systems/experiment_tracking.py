# Experiment Tracking (systems): documentation endpoints served via the
# get_library_docs MCP tool. Verify every URL (curl) before adding
# an entry; the weekly link-check workflow guards against rot.
EXPERIMENT_TRACKING_LIBRARIES: dict[str, dict[str, str | None]] = {
    "wandb": {
        "description": "Experiment tracking, sweeps, and artifact management",
        "domain": "systems",
        "category": "experiment_tracking",
        "official_docs": "https://docs.wandb.ai",
        "github": "https://github.com/wandb/wandb",
        "llms_txt": "https://docs.wandb.ai/llms.txt",
        "llms_full_txt": "https://docs.wandb.ai/llms-full.txt",
    },
    "mlflow": {
        "description": "Open-source ML lifecycle platform (tracking, models, registry)",
        "domain": "systems",
        "category": "experiment_tracking",
        "official_docs": "https://mlflow.org/docs/latest",
        "github": "https://github.com/mlflow/mlflow",
        "llms_txt": "https://mlflow.org/llms.txt",
        "llms_full_txt": None,
    },
}
