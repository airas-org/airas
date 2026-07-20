# Curated dataset registry (see resources/datasets/registry.py for the
# subfield aggregation). HuggingFace dataset IDs and arXiv citations are
# verified on entry; use search_huggingface_hub for un-curated needs.
MULTIMODAL_DATASETS: dict = {
    "textvqa": {
        "description": "Large-scale Multi-modality Models Evaluation Suite Accelerating the development of large-scale multi-modality models (LMMs) with lmms-eval 🏠 Homepage | 📚 Documentation | 🤗 Huggingface Datasets This Dataset This is a formatted version of TextVQA. It is used in our lmms-eval pipeli",
        "huggingface_url": "https://huggingface.co/datasets/lmms-lab/textvqa",
        "task_type": "visual-question-answering",
        "dependent_packages": ["datasets"],
        "code": """from datasets import load_dataset
ds = load_dataset("lmms-lab/textvqa")""",
        "citation": """@misc{singh2019,
  title = {Towards VQA Models That Can Read},
  author = {Amanpreet Singh and Vivek Natarajan and Meet Shah and Yu Jiang and Xinlei Chen and Dhruv Batra and Devi Parikh and Marcus Rohrbach},
  year = {2019},
  eprint = {1904.08920},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/1904.08920}
}""",
    },
    "gqa": {
        "description": "Large-scale Multi-modality Models Evaluation Suite Accelerating the development of large-scale multi-modality models (LMMs) with lmms-eval 🏠 Homepage | 📚 Documentation | 🤗 Huggingface Datasets This Dataset This is a formatted version of GQA. It is used in our lmms-eval pipeline t",
        "huggingface_url": "https://huggingface.co/datasets/lmms-lab/GQA",
        "task_type": "visual-question-answering",
        "dependent_packages": ["datasets"],
        "code": """from datasets import load_dataset
ds = load_dataset("lmms-lab/GQA")""",
        "citation": """@misc{hudson2019,
  title = {GQA: A New Dataset for Real-World Visual Reasoning and Compositional Question Answering},
  author = {Drew A. Hudson and Christopher D. Manning},
  year = {2019},
  eprint = {1902.09506},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/1902.09506}
}""",
    },
    "vqav2": {
        "description": "",
        "huggingface_url": "https://huggingface.co/datasets/lmms-lab/VQAv2",
        "task_type": "visual-question-answering",
        "dependent_packages": ["datasets"],
        "code": """from datasets import load_dataset
ds = load_dataset("lmms-lab/VQAv2")""",
        "citation": """@misc{goyal2016,
  title = {Making the V in VQA Matter: Elevating the Role of Image Understanding in Visual Question Answering},
  author = {Yash Goyal and Tejas Khot and Douglas Summers-Stay and Dhruv Batra and Devi Parikh},
  year = {2016},
  eprint = {1612.00837},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/1612.00837}
}""",
    },
}
