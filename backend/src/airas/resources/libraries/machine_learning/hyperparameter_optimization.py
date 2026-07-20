# machine_learning / hyperparameter_optimization documentation endpoints (shared domain>category
# taxonomy across resources/{libraries,models,datasets}). Verify
# every URL (curl) before adding an entry; the weekly link-check
# workflow guards against rot.
HYPERPARAMETER_OPTIMIZATION_LIBRARIES: dict[str, dict[str, str | None]] = {
    "optuna": {
        "description": "Hyperparameter optimization framework (define-by-run search spaces, pruning)",
        "domain": "machine_learning",
        "category": "hyperparameter_optimization",
        "official_docs": "https://optuna.readthedocs.io/en/stable",
        "github": "https://github.com/optuna/optuna",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
