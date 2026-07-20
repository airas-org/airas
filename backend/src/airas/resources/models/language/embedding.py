# Curated model registry (see resources/models/registry.py for the
# subfield aggregation). HuggingFace URLs and arXiv citations are verified
# on entry; add candidates via search_huggingface_hub for un-curated needs.
TEXT_EMBEDDING_MODELS: dict = {
    "all-minilm-l6-v2": {
        "model_parameters": "23M",
        "model_architecture": "Transformer text-embedding model producing dense sentence/document vectors for retrieval and similarity.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2",
        "task_type": "feature-extraction",
        "dependent_packages": ["sentence-transformers", "torch"],
        "code": """from sentence_transformers import SentenceTransformer
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
embeddings = model.encode(["example sentence"])""",
        "citation": """@misc{reimers2019,
  title = {Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks},
  author = {Nils Reimers and Iryna Gurevych},
  year = {2019},
  eprint = {1908.10084},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/1908.10084}
}""",
    },
    "bge-base-en-v1.5": {
        "model_parameters": "109M",
        "model_architecture": "Transformer text-embedding model producing dense sentence/document vectors for retrieval and similarity.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/BAAI/bge-base-en-v1.5",
        "task_type": "feature-extraction",
        "dependent_packages": ["sentence-transformers", "torch"],
        "code": """from sentence_transformers import SentenceTransformer
model = SentenceTransformer("BAAI/bge-base-en-v1.5")
embeddings = model.encode(["example sentence"])""",
        "citation": """@misc{xiao2023,
  title = {C-Pack: Packed Resources For General Chinese Embeddings},
  author = {Shitao Xiao and Zheng Liu and Peitian Zhang and Niklas Muennighoff and Defu Lian and Jian-Yun Nie},
  year = {2023},
  eprint = {2309.07597},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2309.07597}
}""",
    },
    "gte-base": {
        "model_parameters": "109M",
        "model_architecture": "Transformer text-embedding model producing dense sentence/document vectors for retrieval and similarity.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/thenlper/gte-base",
        "task_type": "feature-extraction",
        "dependent_packages": ["sentence-transformers", "torch"],
        "code": """from sentence_transformers import SentenceTransformer
model = SentenceTransformer("thenlper/gte-base")
embeddings = model.encode(["example sentence"])""",
        "citation": """@misc{li2023,
  title = {Towards General Text Embeddings with Multi-stage Contrastive Learning},
  author = {Zehan Li and Xin Zhang and Yanzhao Zhang and Dingkun Long and Pengjun Xie and Meishan Zhang},
  year = {2023},
  eprint = {2308.03281},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2308.03281}
}""",
    },
    "e5-base-v2": {
        "model_parameters": "109M",
        "model_architecture": "Transformer text-embedding model producing dense sentence/document vectors for retrieval and similarity.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/intfloat/e5-base-v2",
        "task_type": "feature-extraction",
        "dependent_packages": ["sentence-transformers", "torch"],
        "code": """from sentence_transformers import SentenceTransformer
model = SentenceTransformer("intfloat/e5-base-v2")
embeddings = model.encode(["example sentence"])""",
        "citation": """@misc{wang2022,
  title = {Text Embeddings by Weakly-Supervised Contrastive Pre-training},
  author = {Liang Wang and Nan Yang and Xiaolong Huang and Binxing Jiao and Linjun Yang and Daxin Jiang and Rangan Majumder and Furu Wei},
  year = {2022},
  eprint = {2212.03533},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2212.03533}
}""",
    },
}
