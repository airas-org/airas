# Architecture Research libraries: documentation endpoints
# served via the get_library_docs MCP tool. Verify every URL is
# reachable (curl) before adding an entry; the weekly link-check
# workflow guards against rot afterwards.
ARCHITECTURE_RESEARCH_LIBRARIES: dict[str, dict[str, str | None]] = {
    "litgpt": {
        "description": "Hackable implementations of 20+ LLM architectures",
        "category": "architecture_research",
        "official_docs": "https://github.com/Lightning-AI/litgpt",
        "github": "https://github.com/Lightning-AI/litgpt",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "torchtitan": {
        "description": "PyTorch-native pretraining at scale (4D parallelism reference)",
        "category": "architecture_research",
        "official_docs": "https://github.com/pytorch/torchtitan",
        "github": "https://github.com/pytorch/torchtitan",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "mamba": {
        "description": "Selective state space model architecture reference implementation",
        "category": "architecture_research",
        "official_docs": "https://github.com/state-spaces/mamba",
        "github": "https://github.com/state-spaces/mamba",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
