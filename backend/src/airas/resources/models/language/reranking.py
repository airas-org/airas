# Curated model registry — language / reranking. Part of the shared
# domain>category taxonomy across resources/{libraries,models,datasets}.
# HuggingFace URLs and arXiv citations are verified on entry; use
# search_huggingface_hub for un-curated needs.
RERANKING_MODELS: dict = {
    "bge-reranker-base": {
        "description": "",
        "model_parameters": "278M",
        "model_architecture": "Cross-encoder reranker scoring query-document relevance for retrieval.",
        "domain": "language",
        "category": "reranking",
        "task_type": "text-classification",
        "huggingface_url": "https://huggingface.co/BAAI/bge-reranker-base",
        "dependent_packages": ["transformers", "torch"],
        "code": "",
        "citation": """@misc{xiao2023,
  title = {C-Pack: Packed Resources For General Chinese Embeddings},
  author = {Shitao Xiao and Zheng Liu and Peitian Zhang and Niklas Muennighoff and Defu Lian and Jian-Yun Nie},
  year = {2023},
  eprint = {2309.07597},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2309.07597}
}""",
        "training_data_sources": "",
    },
    "jina-reranker-v2": {
        "description": "",
        "model_parameters": "278M",
        "model_architecture": "Cross-encoder reranker scoring query-document relevance for retrieval.",
        "domain": "language",
        "category": "reranking",
        "task_type": "text-classification",
        "huggingface_url": "https://huggingface.co/jinaai/jina-reranker-v2-base-multilingual",
        "dependent_packages": ["transformers", "torch"],
        "code": "",
        "citation": "",
        "training_data_sources": "",
    },
}
