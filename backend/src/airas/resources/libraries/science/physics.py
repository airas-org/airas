# Physics (science): documentation endpoints served via the
# get_library_docs MCP tool. Verify every URL (curl) before adding
# an entry; the weekly link-check workflow guards against rot.
PHYSICS_LIBRARIES: dict[str, dict[str, str | None]] = {
    "physicsnemo": {
        "description": "Physics-ML framework (neural operators, PINNs)",
        "domain": "science",
        "category": "physics",
        "official_docs": "https://docs.nvidia.com/physicsnemo/latest/index.html",
        "github": "https://github.com/NVIDIA/physicsnemo",
        "llms_txt": "https://docs.nvidia.com/llms.txt",
        "llms_full_txt": None,
    },
}
