# graph / graph_learning documentation endpoints (shared domain>category
# taxonomy across resources/{libraries,models,datasets}). Verify
# every URL (curl) before adding an entry; the weekly link-check
# workflow guards against rot.
GRAPH_LEARNING_LIBRARIES: dict[str, dict[str, str | None]] = {
    "torch-geometric": {
        "description": "Graph neural networks for PyTorch",
        "domain": "graph",
        "category": "graph_learning",
        "official_docs": "https://pytorch-geometric.readthedocs.io/en/latest",
        "github": "https://github.com/pyg-team/pytorch_geometric",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
