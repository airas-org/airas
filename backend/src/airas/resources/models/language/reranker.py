# Curated model registry (see resources/models/registry.py for the
# subfield aggregation). HuggingFace URLs and arXiv citations are verified
# on entry; add candidates via search_huggingface_hub for un-curated needs.
RERANKER_MODELS: dict = {
    "bge-reranker-base": {
        "model_parameters": "278M",
        "model_architecture": "Cross-encoder reranker scoring query-document relevance for retrieval.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/BAAI/bge-reranker-base",
        "task_type": "text-classification",
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
    },
    "jina-reranker-v2": {
        "model_parameters": "278M",
        "model_architecture": "Cross-encoder reranker scoring query-document relevance for retrieval.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/jinaai/jina-reranker-v2-base-multilingual",
        "task_type": "text-classification",
        "dependent_packages": ["transformers", "torch"],
        "code": "",
        "citation": "",
    },
}
