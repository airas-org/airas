# Network Analysis (graphs): documentation endpoints served via the
# get_library_docs MCP tool. Verify every URL (curl) before adding
# an entry; the weekly link-check workflow guards against rot.
NETWORK_ANALYSIS_LIBRARIES: dict[str, dict[str, str | None]] = {
    "networkx": {
        "description": "Creation and analysis of graphs and networks",
        "domain": "graphs",
        "category": "network_analysis",
        "official_docs": "https://networkx.org/documentation/stable",
        "github": "https://github.com/networkx/networkx",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "igraph": {
        "description": "Fast graph analysis library (community detection, centrality)",
        "domain": "graphs",
        "category": "network_analysis",
        "official_docs": "https://python.igraph.org/en/stable",
        "github": "https://github.com/igraph/python-igraph",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
