# Curated dataset registry (see resources/datasets/registry.py for the
# subfield aggregation). HuggingFace dataset IDs and arXiv citations are
# verified on entry; use search_huggingface_hub for un-curated needs.
LANGUAGE_MODEL_EVALUATION_DATASETS: dict = {
    "mmlu": {
        "description": "Dataset Card for MMLU Dataset Summary Measuring Massive Multitask Language Understanding by Dan Hendrycks, Collin Burns, Steven Basart, Andy Zou, Mantas Mazeika, Dawn Song, and Jacob Steinhardt (ICLR 2021). This is a massive multitask test consisting of multiple-choice questions ",
        "huggingface_url": "https://huggingface.co/datasets/cais/mmlu",
        "task_type": "multiple-choice",
        "dependent_packages": ["datasets"],
        "code": """from datasets import load_dataset
ds = load_dataset("cais/mmlu")""",
        "citation": """@misc{hendrycks2020,
  title = {Measuring Massive Multitask Language Understanding},
  author = {Dan Hendrycks and Collin Burns and Steven Basart and Andy Zou and Mantas Mazeika and Dawn Song and Jacob Steinhardt},
  year = {2020},
  eprint = {2009.03300},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2009.03300}
}""",
    },
    "hellaswag": {
        "description": "Dataset Card for 'hellaswag' Dataset Summary HellaSwag: Can a Machine Really Finish Your Sentence? is a new dataset for commonsense NLI. A paper was published at ACL2019. Supported Tasks and Leaderboards More Information Needed Languages More Information Needed Dataset Structure ",
        "huggingface_url": "https://huggingface.co/datasets/Rowan/hellaswag",
        "task_type": "multiple-choice",
        "dependent_packages": ["datasets"],
        "code": """from datasets import load_dataset
ds = load_dataset("Rowan/hellaswag")""",
        "citation": """@misc{zellers2019,
  title = {HellaSwag: Can a Machine Really Finish Your Sentence?},
  author = {Rowan Zellers and Ari Holtzman and Yonatan Bisk and Ali Farhadi and Yejin Choi},
  year = {2019},
  eprint = {1905.07830},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/1905.07830}
}""",
    },
    "gsm8k": {
        "description": "Dataset Card for GSM8K Dataset Summary GSM8K (Grade School Math 8K) is a dataset of 8.5K high quality linguistically diverse grade school math word problems. The dataset was created to support the task of question answering on basic mathematical problems that require multi-step r",
        "huggingface_url": "https://huggingface.co/datasets/openai/gsm8k",
        "task_type": "text-generation",
        "dependent_packages": ["datasets"],
        "code": """from datasets import load_dataset
ds = load_dataset("openai/gsm8k")""",
        "citation": """@misc{cobbe2021,
  title = {Training Verifiers to Solve Math Word Problems},
  author = {Karl Cobbe and Vineet Kosaraju and Mohammad Bavarian and Mark Chen and Heewoo Jun and Lukasz Kaiser and Matthias Plappert and Jerry Tworek and Jacob Hilton and Reiichiro Nakano and Christopher Hesse and John Schulman},
  year = {2021},
  eprint = {2110.14168},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2110.14168}
}""",
    },
    "ai2_arc": {
        "description": "Dataset Card for 'ai2_arc' Dataset Summary A new dataset of 7,787 genuine grade-school level, multiple-choice science questions, assembled to encourage research in advanced question-answering. The dataset is partitioned into a Challenge Set and an Easy Set, where the former conta",
        "huggingface_url": "https://huggingface.co/datasets/allenai/ai2_arc",
        "task_type": "multiple-choice",
        "dependent_packages": ["datasets"],
        "code": """from datasets import load_dataset
ds = load_dataset("allenai/ai2_arc")""",
        "citation": """@misc{clark2018,
  title = {Think you have Solved Question Answering? Try ARC, the AI2 Reasoning Challenge},
  author = {Peter Clark and Isaac Cowhey and Oren Etzioni and Tushar Khot and Ashish Sabharwal and Carissa Schoenick and Oyvind Tafjord},
  year = {2018},
  eprint = {1803.05457},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/1803.05457}
}""",
    },
    "truthful_qa": {
        "description": "Dataset Card for truthful_qa Dataset Summary TruthfulQA is a benchmark to measure whether a language model is truthful in generating answers to questions. The benchmark comprises 817 questions that span 38 categories, including health, law, finance and politics. Questions are cra",
        "huggingface_url": "https://huggingface.co/datasets/truthfulqa/truthful_qa",
        "task_type": "multiple-choice",
        "dependent_packages": ["datasets"],
        "code": """from datasets import load_dataset
ds = load_dataset("truthfulqa/truthful_qa")""",
        "citation": """@misc{lin2021,
  title = {TruthfulQA: Measuring How Models Mimic Human Falsehoods},
  author = {Stephanie Lin and Jacob Hilton and Owain Evans},
  year = {2021},
  eprint = {2109.07958},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2109.07958}
}""",
    },
    "winogrande": {
        "description": "Dataset Card for 'winogrande' Dataset Summary WinoGrande is a new collection of 44k problems, inspired by Winograd Schema Challenge (Levesque, Davis, and Morgenstern 2011), but adjusted to improve the scale and robustness against the dataset-specific bias. Formulated as a fill-in",
        "huggingface_url": "https://huggingface.co/datasets/allenai/winogrande",
        "task_type": "multiple-choice",
        "dependent_packages": ["datasets"],
        "code": """from datasets import load_dataset
ds = load_dataset("allenai/winogrande")""",
        "citation": """@misc{sakaguchi2019,
  title = {WinoGrande: An Adversarial Winograd Schema Challenge at Scale},
  author = {Keisuke Sakaguchi and Ronan Le Bras and Chandra Bhagavatula and Yejin Choi},
  year = {2019},
  eprint = {1907.10641},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/1907.10641}
}""",
    },
    "piqa": {
        "description": "To apply eyeshadow without a brush, should I use a cotton swab or a toothpick? Questions requiring this kind of physical commonsense pose a challenge to state-of-the-art natural language understanding systems. The PIQA dataset introduces the task of physical commonsense reasoning",
        "huggingface_url": "https://huggingface.co/datasets/ybisk/piqa",
        "task_type": "multiple-choice",
        "dependent_packages": ["datasets"],
        "code": """from datasets import load_dataset
ds = load_dataset("ybisk/piqa")""",
        "citation": """@misc{bisk2019,
  title = {PIQA: Reasoning about Physical Commonsense in Natural Language},
  author = {Yonatan Bisk and Rowan Zellers and Ronan Le Bras and Jianfeng Gao and Yejin Choi},
  year = {2019},
  eprint = {1911.11641},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/1911.11641}
}""",
    },
}
