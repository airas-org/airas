# systems / inference_serving documentation endpoints (shared domain>category
# taxonomy across resources/{libraries,models,datasets}). Verify
# every URL (curl) before adding an entry; the weekly link-check
# workflow guards against rot.
INFERENCE_SERVING_LIBRARIES: dict[str, dict[str, str | None]] = {
    "vllm": {
        "description": "High-throughput LLM serving (PagedAttention, continuous batching)",
        "domain": "systems",
        "category": "inference_serving",
        "official_docs": "https://docs.vllm.ai",
        "github": "https://github.com/vllm-project/vllm",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "sglang": {
        "description": "Fast LLM serving with RadixAttention and structured generation",
        "domain": "systems",
        "category": "inference_serving",
        "official_docs": "https://docs.sglang.ai",
        "github": "https://github.com/sgl-project/sglang",
        "llms_txt": "https://docs.sglang.ai/llms.txt",
        "llms_full_txt": "https://docs.sglang.ai/llms-full.txt",
    },
    "tensorrt-llm": {
        "description": "NVIDIA-optimized LLM inference engine for TensorRT",
        "domain": "systems",
        "category": "inference_serving",
        "official_docs": "https://nvidia.github.io/TensorRT-LLM",
        "github": "https://github.com/NVIDIA/TensorRT-LLM",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "llama-cpp": {
        "description": "CPU/GPU LLM inference in C/C++ with GGUF quantized models",
        "domain": "systems",
        "category": "inference_serving",
        "official_docs": "https://github.com/ggml-org/llama.cpp",
        "github": "https://github.com/ggml-org/llama.cpp",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "triton-inference-server": {
        "description": "NVIDIA production inference server (multi-framework, ensembles)",
        "domain": "systems",
        "category": "inference_serving",
        "official_docs": "https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs",
        "github": "https://github.com/triton-inference-server/server",
        "llms_txt": "https://docs.nvidia.com/llms.txt",
        "llms_full_txt": None,
    },
}
