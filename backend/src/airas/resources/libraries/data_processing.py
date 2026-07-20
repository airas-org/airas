# Data Processing libraries: documentation endpoints
# served via the get_library_docs MCP tool. Verify every URL is
# reachable (curl) before adding an entry; the weekly link-check
# workflow guards against rot afterwards.
DATA_PROCESSING_LIBRARIES: dict[str, dict[str, str | None]] = {
    "datatrove": {
        "description": "Large-scale text data processing and deduplication pipelines",
        "category": "data_processing",
        "official_docs": "https://github.com/huggingface/datatrove",
        "github": "https://github.com/huggingface/datatrove",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "webdataset": {
        "description": "Streaming tar-based dataset format for large-scale training",
        "category": "data_processing",
        "official_docs": "https://github.com/webdataset/webdataset",
        "github": "https://github.com/webdataset/webdataset",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "polars": {
        "description": "Fast dataframe library (lazy, multi-threaded)",
        "category": "data_processing",
        "official_docs": "https://docs.pola.rs",
        "github": "https://github.com/pola-rs/polars",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "duckdb": {
        "description": "In-process analytical SQL database",
        "category": "data_processing",
        "official_docs": "https://duckdb.org/docs",
        "github": "https://github.com/duckdb/duckdb",
        "llms_txt": "https://duckdb.org/llms.txt",
        "llms_full_txt": None,
    },
    "nemo-curator": {
        "description": "GPU-accelerated data curation for LLM training",
        "category": "data_processing",
        "official_docs": "https://docs.nvidia.com/nemo/curator/latest",
        "github": "https://github.com/NVIDIA-NeMo/Curator",
        "llms_txt": "https://docs.nvidia.com/nemo/curator/latest/llms.txt",
        "llms_full_txt": "https://docs.nvidia.com/nemo/curator/latest/llms-full.txt",
    },
}
