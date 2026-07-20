# Anomaly Detection (machine_learning): documentation endpoints served via the
# get_library_docs MCP tool. Verify every URL (curl) before adding
# an entry; the weekly link-check workflow guards against rot.
ANOMALY_DETECTION_LIBRARIES: dict[str, dict[str, str | None]] = {
    "pyod": {
        "description": "Outlier detection toolkit (50+ algorithms)",
        "domain": "machine_learning",
        "category": "anomaly_detection",
        "official_docs": "https://pyod.readthedocs.io/en/latest",
        "github": "https://github.com/yzhao062/pyod",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "anomalib": {
        "description": "Deep learning anomaly detection for images",
        "domain": "machine_learning",
        "category": "anomaly_detection",
        "official_docs": "https://anomalib.readthedocs.io/en/latest",
        "github": "https://github.com/open-edge-platform/anomalib",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
