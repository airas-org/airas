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
    "mmmu": {
        "description": "MMMU (A Massive Multi-discipline Multimodal Understanding and Reasoning Benchmark for Expert AGI) 🌐 Homepage | 🏆 Leaderboard | 🤗 Dataset | 🤗 Paper | 📖 arXiv | GitHub 🔔News 🛠️[2026-07-10]: Fixed incorrect ground-truth answer labels in validation_Design_15 and validation_Art_Theory",
        "huggingface_url": "https://huggingface.co/datasets/MMMU/MMMU",
        "task_type": "visual-question-answering",
        "dependent_packages": ["datasets"],
        "code": """from datasets import load_dataset
ds = load_dataset("MMMU/MMMU")""",
        "citation": """@misc{yue2023,
  title = {MMMU: A Massive Multi-discipline Multimodal Understanding and Reasoning Benchmark for Expert AGI},
  author = {Xiang Yue and Yuansheng Ni and Kai Zhang and Tianyu Zheng and Ruoqi Liu and Ge Zhang and Samuel Stevens and Dongfu Jiang and Weiming Ren and Yuxuan Sun and Cong Wei and Botao Yu and Ruibin Yuan and Renliang Sun and Ming Yin and Boyuan Zheng and Zhenzhu Yang and Yibo Liu and Wenhao Huang and Huan Sun and Yu Su and Wenhu Chen},
  year = {2023},
  eprint = {2311.16502},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2311.16502}
}""",
    },
    "chartqa": {
        "description": "Dataset Card for 'ChartQA' More Information needed",
        "huggingface_url": "https://huggingface.co/datasets/HuggingFaceM4/ChartQA",
        "task_type": "visual-question-answering",
        "dependent_packages": ["datasets"],
        "code": """from datasets import load_dataset
ds = load_dataset("HuggingFaceM4/ChartQA")""",
        "citation": """@misc{masry2022,
  title = {ChartQA: A Benchmark for Question Answering about Charts with Visual and Logical Reasoning},
  author = {Ahmed Masry and Do Xuan Long and Jia Qing Tan and Shafiq Joty and Enamul Hoque},
  year = {2022},
  eprint = {2203.10244},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2203.10244}
}""",
    },
    "scienceqa": {
        "description": "Dataset Card Creation Guide Dataset Summary Learn to Explain: Multimodal Reasoning via Thought Chains for Science Question Answering Supported Tasks and Leaderboards Multi-modal Multiple Choice Languages English Dataset Structure Data Instances Explore more samples here. {'image'",
        "huggingface_url": "https://huggingface.co/datasets/derek-thomas/ScienceQA",
        "task_type": "visual-question-answering",
        "dependent_packages": ["datasets"],
        "code": """from datasets import load_dataset
ds = load_dataset("derek-thomas/ScienceQA")""",
        "citation": """@misc{lu2022,
  title = {Learn to Explain: Multimodal Reasoning via Thought Chains for Science Question Answering},
  author = {Pan Lu and Swaroop Mishra and Tony Xia and Liang Qiu and Kai-Wei Chang and Song-Chun Zhu and Oyvind Tafjord and Peter Clark and Ashwin Kalyan},
  year = {2022},
  eprint = {2209.09513},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2209.09513}
}""",
    },
}
