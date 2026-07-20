# systems / gpu_computing documentation endpoints (shared domain>category
# taxonomy across resources/{libraries,models,datasets}). Verify
# every URL (curl) before adding an entry; the weekly link-check
# workflow guards against rot.
GPU_COMPUTING_LIBRARIES: dict[str, dict[str, str | None]] = {
    "triton-lang": {
        "description": "Python DSL for writing custom GPU kernels",
        "domain": "systems",
        "category": "gpu_computing",
        "official_docs": "https://triton-lang.org",
        "github": "https://github.com/triton-lang/triton",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "cuda-toolkit": {
        "description": "NVIDIA CUDA Toolkit documentation (runtime, compiler, core libraries)",
        "domain": "systems",
        "category": "gpu_computing",
        "official_docs": "https://docs.nvidia.com/cuda",
        "github": None,
        "llms_txt": "https://docs.nvidia.com/cuda/llms.txt",
        "llms_full_txt": None,
    },
    "nccl": {
        "description": "NVIDIA multi-GPU/multi-node collective communication library",
        "domain": "systems",
        "category": "gpu_computing",
        "official_docs": "https://docs.nvidia.com/deeplearning/nccl/user-guide/docs",
        "github": "https://github.com/NVIDIA/nccl",
        "llms_txt": "https://docs.nvidia.com/llms.txt",
        "llms_full_txt": None,
    },
    "cutlass": {
        "description": "CUDA templates for high-performance GEMM kernels",
        "domain": "systems",
        "category": "gpu_computing",
        "official_docs": "https://docs.nvidia.com/cutlass",
        "github": "https://github.com/NVIDIA/cutlass",
        "llms_txt": "https://docs.nvidia.com/llms.txt",
        "llms_full_txt": None,
    },
    "transformer-engine": {
        "description": "FP8 training acceleration for transformers on NVIDIA GPUs",
        "domain": "systems",
        "category": "gpu_computing",
        "official_docs": "https://docs.nvidia.com/deeplearning/transformer-engine",
        "github": "https://github.com/NVIDIA/TransformerEngine",
        "llms_txt": "https://docs.nvidia.com/llms.txt",
        "llms_full_txt": None,
    },
    "rapids": {
        "description": "GPU dataframes and classical ML (cuDF, cuML)",
        "domain": "systems",
        "category": "gpu_computing",
        "official_docs": "https://docs.rapids.ai",
        "github": "https://github.com/rapidsai/cudf",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
