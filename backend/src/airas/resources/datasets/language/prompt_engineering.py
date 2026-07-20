# Curated dataset registry — language / prompt_engineering. Part of the shared
# domain>category taxonomy across resources/{libraries,models,datasets}.
# HuggingFace dataset IDs and arXiv citations are verified on entry;
# use search_huggingface_hub for un-curated needs.
PROMPT_ENGINEERING_DATASETS: dict = {
    "GSM8K": {
        "description": "Grade School Math 8K is a dataset of 8,500 high-quality, linguistically diverse grade school math word problems. Each problem requires 2 to 8 steps to solve and includes detailed natural language solutions.",
        "domain": "language",
        "category": "prompt_engineering",
        "task_type": ["text-generation"],
        "huggingface_url": "https://huggingface.co/datasets/openai/gsm8k",
        "dependent_packages": ["datasets"],
        "code": """from datasets import load_dataset
dataset = load_dataset('openai/gsm8k', 'main')
train_data = dataset['train']
test_data = dataset['test']""",
        "citation": """@article{cobbe2021gsm8k,
  title={Training Verifiers to Solve Math Word Problems},
  author={Cobbe, Karl and Kosaraju, Vineet and Bavarian, Mohammad and Chen, Mark and Jun, Heewoo and Kaiser, Lukasz and Plappert, Matthias and Tworek, Jerry and Hilton, Jacob and Nakano, Reiichiro and Hesse, Christopher and Schulman, John},
  journal={arXiv preprint arXiv:2110.14168},
  year={2021}
}""",
        "num_training_samples": 7473,
        "num_validation_samples": 1319,
        "language_distribution": "English only (en)",
    },
    "MATH": {
        "description": "The MATH dataset consists of approximately 12,500 challenging competition mathematics problems from high school competitions. Each problem includes a detailed step-by-step solution and difficulty level ranging from middle school to early university level.",
        "domain": "language",
        "category": "prompt_engineering",
        "task_type": ["text-generation"],
        "huggingface_url": "https://huggingface.co/datasets/hendrycks/competition_math",
        "dependent_packages": ["datasets"],
        "code": """from datasets import load_dataset
dataset = load_dataset('hendrycks/competition_math')
train_data = dataset['train']
test_data = dataset['test']""",
        "citation": """@article{hendrycksmath2021,
  title={Measuring Mathematical Problem Solving With the MATH Dataset},
  author={Dan Hendrycks and Collin Burns and Saurav Kadavath and Akul Arora and Steven Basart and Eric Tang and Dawn Song and Jacob Steinhardt},
  journal={arXiv preprint arXiv:2103.03874},
  year={2021}
}""",
        "num_training_samples": 7500,
        "num_validation_samples": 5000,
        "language_distribution": "English only (en)",
    },
    "MMLU": {
        "description": "Massive Multitask Language Understanding (MMLU) is a benchmark covering 57 subjects across STEM, humanities, social sciences, and more. It tests models' world knowledge and problem-solving abilities with multiple-choice questions ranging from elementary to advanced professional level.",
        "domain": "language",
        "category": "prompt_engineering",
        "task_type": ["text-generation"],
        "huggingface_url": "https://huggingface.co/datasets/cais/mmlu",
        "dependent_packages": ["datasets"],
        "code": """from datasets import load_dataset
dataset = load_dataset('cais/mmlu', 'all')
for split in ['auxiliary_train', 'dev', 'test', 'validation']:
    print(f'{split}: {len(dataset[split])}')""",
        "citation": """@article{hendrycks2021measuring,
  title={Measuring Massive Multitask Language Understanding},
  author={Dan Hendrycks and Collin Burns and Steven Basart and Andy Zou and Mantas Mazeika and Dawn Song and Jacob Steinhardt},
  journal={Proceedings of the International Conference on Learning Representations (ICLR)},
  year={2021}
}""",
        "num_training_samples": 285,
        "num_validation_samples": 14042,
        "language_distribution": "English only (en)",
    },
    "TruthfulQA": {
        "description": "TruthfulQA is a benchmark to measure whether language models are truthful in generating answers to questions. The dataset consists of 817 questions across 38 categories including health, law, finance, and politics. Questions are designed to test common misconceptions.",
        "domain": "language",
        "category": "prompt_engineering",
        "task_type": ["text-generation"],
        "huggingface_url": "https://huggingface.co/datasets/truthfulqa/truthful_qa",
        "dependent_packages": ["datasets"],
        "code": """from datasets import load_dataset
dataset = load_dataset('truthfulqa/truthful_qa', 'generation')
validation_data = dataset['validation']""",
        "citation": """@article{lin2021truthfulqa,
  title={TruthfulQA: Measuring How Models Mimic Human Falsehoods},
  author={Stephanie Lin and Jacob Hilton and Owain Evans},
  journal={arXiv preprint arXiv:2109.07958},
  year={2021}
}""",
        "num_training_samples": 0,
        "num_validation_samples": 817,
        "language_distribution": "English only (en)",
    },
    "HumanEval": {
        "description": "HumanEval is an evaluation harness for code generation that measures functional correctness for synthesizing programs from docstrings. It consists of 164 original programming problems designed to assess language comprehension, algorithms, and simple mathematics, with each problem including a function signature, docstring, body, and unit tests.",
        "domain": "language",
        "category": "prompt_engineering",
        "task_type": ["text-generation"],
        "huggingface_url": "https://huggingface.co/datasets/openai/openai_humaneval",
        "dependent_packages": ["datasets"],
        "code": """from datasets import load_dataset
dataset = load_dataset('openai_humaneval')
test_data = dataset['test']
for sample in test_data:
    task_id = sample['task_id']
    prompt = sample['prompt']
    canonical_solution = sample['canonical_solution']
    test = sample['test']
    entry_point = sample['entry_point']""",
        "citation": """@article{chen2021evaluating,
  title={Evaluating Large Language Models Trained on Code},
  author={Mark Chen and Jerry Tworek and Heewoo Jun and Qiming Yuan and Henrique Ponde de Oliveira Pinto and Jared Kaplan and others},
  journal={arXiv preprint arXiv:2107.03374},
  year={2021}
}""",
        "num_training_samples": 0,
        "num_validation_samples": 164,
        "language_distribution": "Natural Language: English (100%), Programming Language: Python (100%)",
    },
    "MBPP": {
        "description": "MBPP (Mostly Basic Python Problems) is a benchmark dataset consisting of around 1,000 crowd-sourced Python programming problems designed to be solvable by entry-level programmers. It covers programming fundamentals, standard library functionality, and common programming patterns, making it ideal for evaluating code generation capabilities.",
        "domain": "language",
        "category": "prompt_engineering",
        "task_type": ["text-generation"],
        "huggingface_url": "https://huggingface.co/datasets/google-research-datasets/mbpp",
        "dependent_packages": ["datasets"],
        "code": """from datasets import load_dataset
dataset_full = load_dataset('mbpp')
dataset_sanitized = load_dataset('mbpp', 'sanitized')
test_data = dataset_full['test']
for sample in test_data:
    task_id = sample['task_id']
    text = sample['text']
    code = sample['code']
    test_list = sample['test_list']""",
        "citation": """@article{austin2021program,
  title={Program Synthesis with Large Language Models},
  author={Austin, Jacob and Odena, Augustus and Nye, Maxwell and Bosma, Maarten and Michalewski, Henryk and Dohan, David and others},
  journal={arXiv preprint arXiv:2108.07732},
  year={2021}
}""",
        "num_training_samples": 374,
        "num_validation_samples": 500,
        "language_distribution": "Natural Language: English (100%), Programming Language: Python (100%)",
    },
    "GPQA": {
        "description": "GPQA (Graduate-Level Google-Proof Q&A Benchmark) is a challenging dataset of 448 multiple-choice questions written by domain experts in biology, physics, and chemistry. The questions are designed to be difficult for highly skilled non-expert validators yet solvable by experts, making it suitable for testing advanced reasoning capabilities.",
        "domain": "language",
        "category": "prompt_engineering",
        "task_type": ["text-generation"],
        "huggingface_url": "https://huggingface.co/datasets/Idavidrein/gpqa",
        "dependent_packages": ["datasets"],
        "code": """from datasets import load_dataset
dataset = load_dataset('Idavidrein/gpqa', 'gpqa_main')
for split in dataset:
    print(f'{split}: {len(dataset[split])}')""",
        "citation": """@article{rein2023gpqa,
  title={GPQA: A Graduate-Level Google-Proof Q&A Benchmark},
  author={David Rein and Betty Li Hou and Asa Cooper Stickland and Jackson Petty and Richard Yuanzhe Pang and Julien Dirani and Julian Michael and Samuel R. Bowman},
  journal={arXiv preprint arXiv:2311.12022},
  year={2023}
}""",
        "num_training_samples": 0,
        "num_validation_samples": 448,
        "language_distribution": "English only (en)",
    },
}
