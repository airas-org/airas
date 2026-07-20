# Post Training libraries: documentation endpoints
# served via the get_library_docs MCP tool. Verify every URL is
# reachable (curl) before adding an entry; the weekly link-check
# workflow guards against rot afterwards.
POST_TRAINING_LIBRARIES: dict[str, dict[str, str | None]] = {
    "trl": {
        "description": "Post-training with RL: SFT, DPO, GRPO, PPO, reward modeling",
        "category": "post_training",
        "official_docs": "https://huggingface.co/docs/trl",
        "github": "https://github.com/huggingface/trl",
        "llms_txt": "https://huggingface.co/docs/trl/llms.txt",
        "llms_full_txt": "https://huggingface.co/docs/trl/llms-full.txt",
    },
    "openrlhf": {
        "description": "High-performance RLHF framework built on Ray and vLLM",
        "category": "post_training",
        "official_docs": "https://openrlhf.readthedocs.io/en/latest",
        "github": "https://github.com/OpenRLHF/OpenRLHF",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "verl": {
        "description": "RL training library for LLMs (volcano engine RLHF)",
        "category": "post_training",
        "official_docs": "https://verl.readthedocs.io/en/latest",
        "github": "https://github.com/verl-project/verl",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
