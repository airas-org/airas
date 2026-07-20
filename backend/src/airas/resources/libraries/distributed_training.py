# Distributed Training libraries: documentation endpoints
# served via the get_library_docs MCP tool. Verify every URL is
# reachable (curl) before adding an entry; the weekly link-check
# workflow guards against rot afterwards.
DISTRIBUTED_TRAINING_LIBRARIES: dict[str, dict[str, str | None]] = {
    "deepspeed": {
        "description": "Distributed training/inference with ZeRO memory optimization",
        "category": "distributed_training",
        "official_docs": "https://www.deepspeed.ai",
        "github": "https://github.com/deepspeedai/DeepSpeed",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "accelerate": {
        "description": "Run the same PyTorch code on any distributed setup",
        "category": "distributed_training",
        "official_docs": "https://huggingface.co/docs/accelerate",
        "github": "https://github.com/huggingface/accelerate",
        "llms_txt": "https://huggingface.co/docs/accelerate/llms.txt",
        "llms_full_txt": "https://huggingface.co/docs/accelerate/llms-full.txt",
    },
    "pytorch-lightning": {
        "description": "High-level PyTorch training framework (Trainer, callbacks, DDP)",
        "category": "distributed_training",
        "official_docs": "https://lightning.ai/docs/pytorch/stable",
        "github": "https://github.com/Lightning-AI/pytorch-lightning",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "ray": {
        "description": "Distributed compute for scaling training, tuning, and serving",
        "category": "distributed_training",
        "official_docs": "https://docs.ray.io/en/latest",
        "github": "https://github.com/ray-project/ray",
        "llms_txt": "https://docs.ray.io/llms.txt",
        "llms_full_txt": "https://docs.ray.io/llms-full.txt",
    },
    "megatron-core": {
        "description": "NVIDIA library for large-scale transformer training (TP/PP/SP)",
        "category": "distributed_training",
        "official_docs": "https://docs.nvidia.com/megatron-core/developer-guide/latest",
        "github": "https://github.com/NVIDIA/Megatron-LM",
        "llms_txt": "https://docs.nvidia.com/llms.txt",
        "llms_full_txt": None,
    },
    "nemo": {
        "description": "NVIDIA framework for large-scale LLM and multimodal training",
        "category": "distributed_training",
        "official_docs": "https://docs.nvidia.com/nemo-framework/user-guide/latest",
        "github": "https://github.com/NVIDIA-NeMo",
        "llms_txt": "https://docs.nvidia.com/nemo-framework/llms.txt",
        "llms_full_txt": None,
    },
}
