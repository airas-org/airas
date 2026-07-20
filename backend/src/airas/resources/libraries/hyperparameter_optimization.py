# Hyperparameter Optimization libraries: documentation endpoints
# served via the get_library_docs MCP tool. Verify every URL is
# reachable (curl) before adding an entry; the weekly link-check
# workflow guards against rot afterwards.
HYPERPARAMETER_OPTIMIZATION_LIBRARIES: dict[str, dict[str, str | None]] = {
    "optuna": {
        "description": "Hyperparameter optimization framework (define-by-run search spaces, pruning)",
        "category": "hyperparameter_optimization",
        "official_docs": "https://optuna.readthedocs.io/en/stable",
        "github": "https://github.com/optuna/optuna",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "ax": {
        "description": "Adaptive experimentation platform for A/B tests and Bayesian optimization",
        "category": "hyperparameter_optimization",
        "official_docs": "https://ax.dev",
        "github": "https://github.com/facebook/Ax",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "botorch": {
        "description": "Bayesian optimization library built on PyTorch",
        "category": "hyperparameter_optimization",
        "official_docs": "https://botorch.org",
        "github": "https://github.com/meta-pytorch/botorch",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
