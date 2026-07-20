# Curated dataset registry (see resources/datasets/registry.py for the
# subfield aggregation). HuggingFace dataset IDs and arXiv citations are
# verified on entry; use search_huggingface_hub for un-curated needs.
NATURAL_LANGUAGE_PROCESSING_DATASETS: dict = {
    "squad": {
        "description": "Dataset Card for SQuAD Dataset Summary Stanford Question Answering Dataset (SQuAD) is a reading comprehension dataset, consisting of questions posed by crowdworkers on a set of Wikipedia articles, where the answer to every question is a segment of text, or span, from the correspo",
        "huggingface_url": "https://huggingface.co/datasets/rajpurkar/squad",
        "task_type": "question-answering",
        "dependent_packages": ["datasets"],
        "code": """from datasets import load_dataset
ds = load_dataset("rajpurkar/squad")""",
        "citation": """@misc{rajpurkar2016,
  title = {SQuAD: 100,000+ Questions for Machine Comprehension of Text},
  author = {Pranav Rajpurkar and Jian Zhang and Konstantin Lopyrev and Percy Liang},
  year = {2016},
  eprint = {1606.05250},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/1606.05250}
}""",
    },
    "trivia_qa": {
        "description": "Dataset Card for 'trivia_qa' Dataset Summary TriviaqQA is a reading comprehension dataset containing over 650K question-answer-evidence triples. TriviaqQA includes 95K question-answer pairs authored by trivia enthusiasts and independently gathered evidence documents, six per ques",
        "huggingface_url": "https://huggingface.co/datasets/mandarjoshi/trivia_qa",
        "task_type": "question-answering",
        "dependent_packages": ["datasets"],
        "code": """from datasets import load_dataset
ds = load_dataset("mandarjoshi/trivia_qa")""",
        "citation": """@misc{joshi2017,
  title = {TriviaQA: A Large Scale Distantly Supervised Challenge Dataset for Reading Comprehension},
  author = {Mandar Joshi and Eunsol Choi and Daniel S. Weld and Luke Zettlemoyer},
  year = {2017},
  eprint = {1705.03551},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/1705.03551}
}""",
    },
    "cnn_dailymail": {
        "description": "Dataset Card for CNN Dailymail Dataset Dataset Summary The CNN / DailyMail Dataset is an English-language dataset containing just over 300k unique news articles as written by journalists at CNN and the Daily Mail. The current version supports both extractive and abstractive summa",
        "huggingface_url": "https://huggingface.co/datasets/abisee/cnn_dailymail",
        "task_type": "summarization",
        "dependent_packages": ["datasets"],
        "code": """from datasets import load_dataset
ds = load_dataset("abisee/cnn_dailymail")""",
        "citation": "",
    },
    "xsum": {
        "description": "Dataset Card for 'xsum' Dataset Summary Extreme Summarization (XSum) Dataset. There are three features: document: Input news article. summary: One sentence summary of the article. id: BBC ID of the article. Supported Tasks and Leaderboards More Information Needed Languages More I",
        "huggingface_url": "https://huggingface.co/datasets/EdinburghNLP/xsum",
        "task_type": "summarization",
        "dependent_packages": ["datasets"],
        "code": """from datasets import load_dataset
ds = load_dataset("EdinburghNLP/xsum")""",
        "citation": """@misc{narayan2018,
  title = {Don't Give Me the Details, Just the Summary! Topic-Aware Convolutional Neural Networks for Extreme Summarization},
  author = {Shashi Narayan and Shay B. Cohen and Mirella Lapata},
  year = {2018},
  eprint = {1808.08745},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/1808.08745}
}""",
    },
    "multi_nli": {
        "description": "Dataset Card for Multi-Genre Natural Language Inference (MultiNLI) Dataset Summary The Multi-Genre Natural Language Inference (MultiNLI) corpus is a crowd-sourced collection of 433k sentence pairs annotated with textual entailment information. The corpus is modeled on the SNLI co",
        "huggingface_url": "https://huggingface.co/datasets/nyu-mll/multi_nli",
        "task_type": "text-classification",
        "dependent_packages": ["datasets"],
        "code": """from datasets import load_dataset
ds = load_dataset("nyu-mll/multi_nli")""",
        "citation": """@misc{williams2017,
  title = {A Broad-Coverage Challenge Corpus for Sentence Understanding through Inference},
  author = {Adina Williams and Nikita Nangia and Samuel R. Bowman},
  year = {2017},
  eprint = {1704.05426},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/1704.05426}
}""",
    },
    "glue": {
        "description": "Dataset Card for GLUE Dataset Summary GLUE, the General Language Understanding Evaluation benchmark (https://gluebenchmark.com/) is a collection of resources for training, evaluating, and analyzing natural language understanding systems. Supported Tasks and Leaderboards The leade",
        "huggingface_url": "https://huggingface.co/datasets/nyu-mll/glue",
        "task_type": "text-classification",
        "dependent_packages": ["datasets"],
        "code": """from datasets import load_dataset
ds = load_dataset("nyu-mll/glue")""",
        "citation": """@misc{wang2018,
  title = {GLUE: A Multi-Task Benchmark and Analysis Platform for Natural Language Understanding},
  author = {Alex Wang and Amanpreet Singh and Julian Michael and Felix Hill and Omer Levy and Samuel R. Bowman},
  year = {2018},
  eprint = {1804.07461},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/1804.07461}
}""",
    },
}
