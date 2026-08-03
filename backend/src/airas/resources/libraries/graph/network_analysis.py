# graph / network_analysis documentation endpoints (shared domain>category
# taxonomy across resources/{libraries,models,datasets}). Verify
# every URL (curl) before adding an entry; the weekly link-check
# workflow guards against rot.
NETWORK_ANALYSIS_LIBRARIES: dict[str, dict[str, str | None]] = {
    "networkx": {
        "description": "Creation and analysis of graphs and networks",
        "domain": "graph",
        "category": "network_analysis",
        "official_docs": "https://networkx.org/documentation/stable",
        "github": "https://github.com/networkx/networkx",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "igraph": {
        "description": "Fast graph analysis library (community detection, centrality)",
        "domain": "graph",
        "category": "network_analysis",
        "official_docs": "https://python.igraph.org/en/stable",
        "github": "https://github.com/igraph/python-igraph",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
