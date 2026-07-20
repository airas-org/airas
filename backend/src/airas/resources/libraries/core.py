# Core libraries: documentation endpoints
# served via the get_library_docs MCP tool. Verify every URL is
# reachable (curl) before adding an entry; the weekly link-check
# workflow guards against rot afterwards.
CORE_LIBRARIES: dict[str, dict[str, str | None]] = {
    "transformers": {
        "description": "Pretrained model library and training utilities (Trainer)",
        "category": "core",
        "official_docs": "https://huggingface.co/docs/transformers",
        "github": "https://github.com/huggingface/transformers",
        "llms_txt": "https://huggingface.co/docs/transformers/llms.txt",
        "llms_full_txt": "https://huggingface.co/docs/transformers/llms-full.txt",
    },
    "datasets": {
        "description": "Loading, processing, and streaming of ML datasets",
        "category": "core",
        "official_docs": "https://huggingface.co/docs/datasets",
        "github": "https://github.com/huggingface/datasets",
        "llms_txt": "https://huggingface.co/docs/datasets/llms.txt",
        "llms_full_txt": "https://huggingface.co/docs/datasets/llms-full.txt",
    },
    "pytorch": {
        "description": "Core deep learning framework",
        "category": "core",
        "official_docs": "https://docs.pytorch.org/docs/stable",
        "github": "https://github.com/pytorch/pytorch",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
