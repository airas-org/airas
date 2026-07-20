# Optimization libraries: documentation endpoints
# served via the get_library_docs MCP tool. Verify every URL is
# reachable (curl) before adding an entry; the weekly link-check
# workflow guards against rot afterwards.
OPTIMIZATION_LIBRARIES: dict[str, dict[str, str | None]] = {
    "bitsandbytes": {
        "description": "8-bit/4-bit quantization and optimizers for PyTorch",
        "category": "optimization",
        "official_docs": "https://huggingface.co/docs/bitsandbytes",
        "github": "https://github.com/bitsandbytes-foundation/bitsandbytes",
        "llms_txt": "https://huggingface.co/docs/bitsandbytes/llms.txt",
        "llms_full_txt": "https://huggingface.co/docs/bitsandbytes/llms-full.txt",
    },
    "flash-attention": {
        "description": "Fused attention kernels (FlashAttention 2/3) for memory and speed",
        "category": "optimization",
        "official_docs": "https://github.com/Dao-AILab/flash-attention",
        "github": "https://github.com/Dao-AILab/flash-attention",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "torchao": {
        "description": "PyTorch-native quantization and sparsity (weight-only, QAT, float8)",
        "category": "optimization",
        "official_docs": "https://docs.pytorch.org/ao",
        "github": "https://github.com/pytorch/ao",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "llm-compressor": {
        "description": "Model compression (GPTQ, AWQ, SmoothQuant, sparsity) for vLLM deployment",
        "category": "optimization",
        "official_docs": "https://docs.vllm.ai/projects/llm-compressor/en/latest",
        "github": "https://github.com/vllm-project/llm-compressor",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
