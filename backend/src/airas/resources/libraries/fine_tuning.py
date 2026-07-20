# Fine Tuning libraries: documentation endpoints
# served via the get_library_docs MCP tool. Verify every URL is
# reachable (curl) before adding an entry; the weekly link-check
# workflow guards against rot afterwards.
FINE_TUNING_LIBRARIES: dict[str, dict[str, str | None]] = {
    "unsloth": {
        "description": "Memory-efficient LLM fine-tuning and RL (2x faster, ~70% less VRAM)",
        "category": "fine_tuning",
        "official_docs": "https://docs.unsloth.ai",
        "github": "https://github.com/unslothai/unsloth",
        "llms_txt": "https://docs.unsloth.ai/llms.txt",
        "llms_full_txt": "https://docs.unsloth.ai/llms-full.txt",
    },
    "axolotl": {
        "description": "Config-driven post-training for LLMs (full/LoRA/QLoRA fine-tuning)",
        "category": "fine_tuning",
        "official_docs": "https://docs.axolotl.ai",
        "github": "https://github.com/axolotl-ai-cloud/axolotl",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "peft": {
        "description": "Parameter-efficient fine-tuning methods (LoRA, prompt tuning, ...)",
        "category": "fine_tuning",
        "official_docs": "https://huggingface.co/docs/peft",
        "github": "https://github.com/huggingface/peft",
        "llms_txt": "https://huggingface.co/docs/peft/llms.txt",
        "llms_full_txt": "https://huggingface.co/docs/peft/llms-full.txt",
    },
    "llama-factory": {
        "description": "Unified fine-tuning framework for 100+ LLMs/VLMs with a web UI",
        "category": "fine_tuning",
        "official_docs": "https://llamafactory.readthedocs.io/en/latest",
        "github": "https://github.com/hiyouga/LlamaFactory",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
