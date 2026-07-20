# Graph Learning libraries: documentation endpoints
# served via the get_library_docs MCP tool. Verify every URL is
# reachable (curl) before adding an entry; the weekly link-check
# workflow guards against rot afterwards.
GRAPH_LEARNING_LIBRARIES: dict[str, dict[str, str | None]] = {
    "torch-geometric": {
        "description": "Graph neural networks for PyTorch",
        "category": "graph_learning",
        "official_docs": "https://pytorch-geometric.readthedocs.io/en/latest",
        "github": "https://github.com/pyg-team/pytorch_geometric",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
