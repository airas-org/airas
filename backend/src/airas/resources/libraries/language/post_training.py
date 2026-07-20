# language / post_training documentation endpoints (shared domain>category
# taxonomy across resources/{libraries,models,datasets}). Verify
# every URL (curl) before adding an entry; the weekly link-check
# workflow guards against rot.
POST_TRAINING_LIBRARIES: dict[str, dict[str, str | None]] = {
    "trl": {
        "description": "Post-training with RL: SFT, DPO, GRPO, PPO, reward modeling",
        "domain": "language",
        "category": "post_training",
        "official_docs": "https://huggingface.co/docs/trl",
        "github": "https://github.com/huggingface/trl",
        "llms_txt": "https://huggingface.co/docs/trl/llms.txt",
        "llms_full_txt": "https://huggingface.co/docs/trl/llms-full.txt",
    },
    "openrlhf": {
        "description": "High-performance RLHF framework built on Ray and vLLM",
        "domain": "language",
        "category": "post_training",
        "official_docs": "https://openrlhf.readthedocs.io/en/latest",
        "github": "https://github.com/OpenRLHF/OpenRLHF",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "verl": {
        "description": "RL training library for LLMs (volcano engine RLHF)",
        "domain": "language",
        "category": "post_training",
        "official_docs": "https://verl.readthedocs.io/en/latest",
        "github": "https://github.com/verl-project/verl",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
