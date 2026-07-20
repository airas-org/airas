# Inference Serving libraries: documentation endpoints
# served via the get_library_docs MCP tool. Verify every URL is
# reachable (curl) before adding an entry; the weekly link-check
# workflow guards against rot afterwards.
INFERENCE_SERVING_LIBRARIES: dict[str, dict[str, str | None]] = {
    "vllm": {
        "description": "High-throughput LLM serving (PagedAttention, continuous batching)",
        "category": "inference_serving",
        "official_docs": "https://docs.vllm.ai",
        "github": "https://github.com/vllm-project/vllm",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "sglang": {
        "description": "Fast LLM serving with RadixAttention and structured generation",
        "category": "inference_serving",
        "official_docs": "https://docs.sglang.ai",
        "github": "https://github.com/sgl-project/sglang",
        "llms_txt": "https://docs.sglang.ai/llms.txt",
        "llms_full_txt": "https://docs.sglang.ai/llms-full.txt",
    },
    "tensorrt-llm": {
        "description": "NVIDIA-optimized LLM inference engine for TensorRT",
        "category": "inference_serving",
        "official_docs": "https://nvidia.github.io/TensorRT-LLM",
        "github": "https://github.com/NVIDIA/TensorRT-LLM",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "llama-cpp": {
        "description": "CPU/GPU LLM inference in C/C++ with GGUF quantized models",
        "category": "inference_serving",
        "official_docs": "https://github.com/ggml-org/llama.cpp",
        "github": "https://github.com/ggml-org/llama.cpp",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "triton-inference-server": {
        "description": "NVIDIA production inference server (multi-framework, ensembles)",
        "category": "inference_serving",
        "official_docs": "https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs",
        "github": "https://github.com/triton-inference-server/server",
        "llms_txt": "https://docs.nvidia.com/llms.txt",
        "llms_full_txt": None,
    },
}
