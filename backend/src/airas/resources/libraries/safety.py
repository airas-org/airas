# Safety libraries: documentation endpoints
# served via the get_library_docs MCP tool. Verify every URL is
# reachable (curl) before adding an entry; the weekly link-check
# workflow guards against rot afterwards.
SAFETY_LIBRARIES: dict[str, dict[str, str | None]] = {
    "nemo-guardrails": {
        "description": "Programmable guardrails for LLM applications",
        "category": "safety",
        "official_docs": "https://docs.nvidia.com/nemo/guardrails",
        "github": "https://github.com/NVIDIA-NeMo/Guardrails",
        "llms_txt": "https://docs.nvidia.com/nemo/guardrails/llms.txt",
        "llms_full_txt": "https://docs.nvidia.com/nemo/guardrails/llms-full.txt",
    },
}
