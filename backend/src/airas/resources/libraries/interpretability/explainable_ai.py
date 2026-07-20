# interpretability / explainable_ai documentation endpoints (shared domain>category
# taxonomy across resources/{libraries,models,datasets}). Verify
# every URL (curl) before adding an entry; the weekly link-check
# workflow guards against rot.
EXPLAINABLE_AI_LIBRARIES: dict[str, dict[str, str | None]] = {
    "captum": {
        "description": "Model attribution and interpretability for PyTorch",
        "domain": "interpretability",
        "category": "explainable_ai",
        "official_docs": "https://captum.ai",
        "github": "https://github.com/meta-pytorch/captum",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "shap": {
        "description": "Game-theoretic feature attribution (Shapley values)",
        "domain": "interpretability",
        "category": "explainable_ai",
        "official_docs": "https://shap.readthedocs.io/en/latest",
        "github": "https://github.com/shap/shap",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "interpretml": {
        "description": "Glassbox models and blackbox explanations",
        "domain": "interpretability",
        "category": "explainable_ai",
        "official_docs": "https://interpret.ml/docs",
        "github": "https://github.com/interpretml/interpret",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
