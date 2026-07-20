# systems / distributed_training documentation endpoints (shared domain>category
# taxonomy across resources/{libraries,models,datasets}). Verify
# every URL (curl) before adding an entry; the weekly link-check
# workflow guards against rot.
DISTRIBUTED_TRAINING_LIBRARIES: dict[str, dict[str, str | None]] = {
    "deepspeed": {
        "description": "Distributed training/inference with ZeRO memory optimization",
        "domain": "systems",
        "category": "distributed_training",
        "official_docs": "https://www.deepspeed.ai",
        "github": "https://github.com/deepspeedai/DeepSpeed",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "accelerate": {
        "description": "Run the same PyTorch code on any distributed setup",
        "domain": "systems",
        "category": "distributed_training",
        "official_docs": "https://huggingface.co/docs/accelerate",
        "github": "https://github.com/huggingface/accelerate",
        "llms_txt": "https://huggingface.co/docs/accelerate/llms.txt",
        "llms_full_txt": "https://huggingface.co/docs/accelerate/llms-full.txt",
    },
    "pytorch-lightning": {
        "description": "High-level PyTorch training framework (Trainer, callbacks, DDP)",
        "domain": "systems",
        "category": "distributed_training",
        "official_docs": "https://lightning.ai/docs/pytorch/stable",
        "github": "https://github.com/Lightning-AI/pytorch-lightning",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "ray": {
        "description": "Distributed compute for scaling training, tuning, and serving",
        "domain": "systems",
        "category": "distributed_training",
        "official_docs": "https://docs.ray.io/en/latest",
        "github": "https://github.com/ray-project/ray",
        "llms_txt": "https://docs.ray.io/llms.txt",
        "llms_full_txt": "https://docs.ray.io/llms-full.txt",
    },
    "megatron-core": {
        "description": "NVIDIA library for large-scale transformer training (TP/PP/SP)",
        "domain": "systems",
        "category": "distributed_training",
        "official_docs": "https://docs.nvidia.com/megatron-core/developer-guide/latest",
        "github": "https://github.com/NVIDIA/Megatron-LM",
        "llms_txt": "https://docs.nvidia.com/llms.txt",
        "llms_full_txt": None,
    },
    "nemo": {
        "description": "NVIDIA framework for large-scale LLM and multimodal training",
        "domain": "systems",
        "category": "distributed_training",
        "official_docs": "https://docs.nvidia.com/nemo-framework/user-guide/latest",
        "github": "https://github.com/NVIDIA-NeMo",
        "llms_txt": "https://docs.nvidia.com/nemo-framework/llms.txt",
        "llms_full_txt": None,
    },
}
