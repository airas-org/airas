# Statistical Ml (machine_learning): documentation endpoints served via the
# get_library_docs MCP tool. Verify every URL (curl) before adding
# an entry; the weekly link-check workflow guards against rot.
STATISTICAL_ML_LIBRARIES: dict[str, dict[str, str | None]] = {
    "scikit-learn": {
        "description": "Classical ML algorithms, model selection, and metrics",
        "domain": "machine_learning",
        "category": "statistical_ml",
        "official_docs": "https://scikit-learn.org/stable",
        "github": "https://github.com/scikit-learn/scikit-learn",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "xgboost": {
        "description": "Gradient boosting library (regression, classification, ranking)",
        "domain": "machine_learning",
        "category": "statistical_ml",
        "official_docs": "https://xgboost.readthedocs.io/en/stable",
        "github": "https://github.com/dmlc/xgboost",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "lightgbm": {
        "description": "Fast gradient boosting framework by Microsoft",
        "domain": "machine_learning",
        "category": "statistical_ml",
        "official_docs": "https://lightgbm.readthedocs.io/en/stable",
        "github": "https://github.com/lightgbm-org/LightGBM",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "catboost": {
        "description": "Gradient boosting with native categorical feature support",
        "domain": "machine_learning",
        "category": "statistical_ml",
        "official_docs": "https://catboost.ai/docs/en",
        "github": "https://github.com/catboost/catboost",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
