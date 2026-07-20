# language / fine_tuning documentation endpoints (shared domain>category
# taxonomy across resources/{libraries,models,datasets}). Verify
# every URL (curl) before adding an entry; the weekly link-check
# workflow guards against rot.
FINE_TUNING_LIBRARIES: dict[str, dict[str, str | None]] = {
    "unsloth": {
        "description": "Memory-efficient LLM fine-tuning and RL (2x faster, ~70% less VRAM)",
        "domain": "language",
        "category": "fine_tuning",
        "official_docs": "https://docs.unsloth.ai",
        "github": "https://github.com/unslothai/unsloth",
        "llms_txt": "https://docs.unsloth.ai/llms.txt",
        "llms_full_txt": "https://docs.unsloth.ai/llms-full.txt",
    },
    "axolotl": {
        "description": "Config-driven post-training for LLMs (full/LoRA/QLoRA fine-tuning)",
        "domain": "language",
        "category": "fine_tuning",
        "official_docs": "https://docs.axolotl.ai",
        "github": "https://github.com/axolotl-ai-cloud/axolotl",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "peft": {
        "description": "Parameter-efficient fine-tuning methods (LoRA, prompt tuning, ...)",
        "domain": "language",
        "category": "fine_tuning",
        "official_docs": "https://huggingface.co/docs/peft",
        "github": "https://github.com/huggingface/peft",
        "llms_txt": "https://huggingface.co/docs/peft/llms.txt",
        "llms_full_txt": "https://huggingface.co/docs/peft/llms-full.txt",
    },
    "llama-factory": {
        "description": "Unified fine-tuning framework for 100+ LLMs/VLMs with a web UI",
        "domain": "language",
        "category": "fine_tuning",
        "official_docs": "https://llamafactory.readthedocs.io/en/latest",
        "github": "https://github.com/hiyouga/LlamaFactory",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
