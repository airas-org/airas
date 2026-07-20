# Classical Ml libraries: documentation endpoints
# served via the get_library_docs MCP tool. Verify every URL is
# reachable (curl) before adding an entry; the weekly link-check
# workflow guards against rot afterwards.
CLASSICAL_ML_LIBRARIES: dict[str, dict[str, str | None]] = {
    "scikit-learn": {
        "description": "Classical ML algorithms, model selection, and metrics",
        "category": "classical_ml",
        "official_docs": "https://scikit-learn.org/stable",
        "github": "https://github.com/scikit-learn/scikit-learn",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
