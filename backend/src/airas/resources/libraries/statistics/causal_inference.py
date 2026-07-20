# Causal Inference (statistics): documentation endpoints served via the
# get_library_docs MCP tool. Verify every URL (curl) before adding
# an entry; the weekly link-check workflow guards against rot.
CAUSAL_INFERENCE_LIBRARIES: dict[str, dict[str, str | None]] = {
    "dowhy": {
        "description": "Causal inference with explicit assumptions and refutation tests",
        "domain": "statistics",
        "category": "causal_inference",
        "official_docs": "https://www.pywhy.org/dowhy",
        "github": "https://github.com/py-why/dowhy",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "econml": {
        "description": "Heterogeneous treatment effect estimation (DML, DR, meta-learners)",
        "domain": "statistics",
        "category": "causal_inference",
        "official_docs": "https://econml.azurewebsites.net",
        "github": "https://github.com/py-why/EconML",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "causalml": {
        "description": "Uplift modeling and causal machine learning",
        "domain": "statistics",
        "category": "causal_inference",
        "official_docs": "https://causalml.readthedocs.io/en/latest",
        "github": "https://github.com/uber/causalml",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
