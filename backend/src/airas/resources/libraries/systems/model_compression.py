# systems / model_compression documentation endpoints (shared domain>category
# taxonomy across resources/{libraries,models,datasets}). Verify
# every URL (curl) before adding an entry; the weekly link-check
# workflow guards against rot.
MODEL_COMPRESSION_LIBRARIES: dict[str, dict[str, str | None]] = {
    "bitsandbytes": {
        "description": "8-bit/4-bit quantization and optimizers for PyTorch",
        "domain": "systems",
        "category": "model_compression",
        "official_docs": "https://huggingface.co/docs/bitsandbytes",
        "github": "https://github.com/bitsandbytes-foundation/bitsandbytes",
        "llms_txt": "https://huggingface.co/docs/bitsandbytes/llms.txt",
        "llms_full_txt": "https://huggingface.co/docs/bitsandbytes/llms-full.txt",
    },
    "flash-attention": {
        "description": "Fused attention kernels (FlashAttention 2/3) for memory and speed",
        "domain": "systems",
        "category": "model_compression",
        "official_docs": "https://github.com/Dao-AILab/flash-attention",
        "github": "https://github.com/Dao-AILab/flash-attention",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "torchao": {
        "description": "PyTorch-native quantization and sparsity (weight-only, QAT, float8)",
        "domain": "systems",
        "category": "model_compression",
        "official_docs": "https://docs.pytorch.org/ao",
        "github": "https://github.com/pytorch/ao",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "llm-compressor": {
        "description": "Model compression (GPTQ, AWQ, SmoothQuant, sparsity) for vLLM deployment",
        "domain": "systems",
        "category": "model_compression",
        "official_docs": "https://docs.vllm.ai/projects/llm-compressor/en/latest",
        "github": "https://github.com/vllm-project/llm-compressor",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
