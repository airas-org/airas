# Curated model registry (see resources/models/registry.py for the
# subfield aggregation). HuggingFace URLs and arXiv citations are verified
# on entry; add candidates via search_huggingface_hub for un-curated needs.
ENCODER_LANGUAGE_MODELS: dict = {
    "bert-base-uncased": {
        "model_parameters": "110M",
        "model_architecture": "Encoder-only (BERT-style) transformer trained with masked language modeling; used for embeddings and fine-tuned classification/token tasks.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/google-bert/bert-base-uncased",
        "task_type": "fill-mask",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("fill-mask", model="google-bert/bert-base-uncased")""",
        "citation": """@misc{devlin2018,
  title = {BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding},
  author = {Jacob Devlin and Ming-Wei Chang and Kenton Lee and Kristina Toutanova},
  year = {2018},
  eprint = {1810.04805},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/1810.04805}
}""",
    },
    "roberta-base": {
        "model_parameters": "125M",
        "model_architecture": "Encoder-only (BERT-style) transformer trained with masked language modeling; used for embeddings and fine-tuned classification/token tasks.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/FacebookAI/roberta-base",
        "task_type": "fill-mask",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("fill-mask", model="FacebookAI/roberta-base")""",
        "citation": """@misc{liu2019,
  title = {RoBERTa: A Robustly Optimized BERT Pretraining Approach},
  author = {Yinhan Liu and Myle Ott and Naman Goyal and Jingfei Du and Mandar Joshi and Danqi Chen and Omer Levy and Mike Lewis and Luke Zettlemoyer and Veselin Stoyanov},
  year = {2019},
  eprint = {1907.11692},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/1907.11692}
}""",
    },
    "deberta-v3-base": {
        "model_parameters": "Unknown",
        "model_architecture": "Encoder-only (BERT-style) transformer trained with masked language modeling; used for embeddings and fine-tuned classification/token tasks.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/microsoft/deberta-v3-base",
        "task_type": "fill-mask",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("fill-mask", model="microsoft/deberta-v3-base")""",
        "citation": """@misc{he2021,
  title = {DeBERTaV3: Improving DeBERTa using ELECTRA-Style Pre-Training with Gradient-Disentangled Embedding Sharing},
  author = {Pengcheng He and Jianfeng Gao and Weizhu Chen},
  year = {2021},
  eprint = {2111.09543},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2111.09543}
}""",
    },
    "electra-base": {
        "model_parameters": "Unknown",
        "model_architecture": "Encoder-only (BERT-style) transformer trained with masked language modeling; used for embeddings and fine-tuned classification/token tasks.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/google/electra-base-discriminator",
        "task_type": "fill-mask",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("fill-mask", model="google/electra-base-discriminator")""",
        "citation": """@misc{clark2020,
  title = {ELECTRA: Pre-training Text Encoders as Discriminators Rather Than Generators},
  author = {Kevin Clark and Minh-Thang Luong and Quoc V. Le and Christopher D. Manning},
  year = {2020},
  eprint = {2003.10555},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2003.10555}
}""",
    },
    "distilbert-base-uncased": {
        "model_parameters": "67M",
        "model_architecture": "Encoder-only (BERT-style) transformer trained with masked language modeling; used for embeddings and fine-tuned classification/token tasks.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/distilbert/distilbert-base-uncased",
        "task_type": "fill-mask",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("fill-mask", model="distilbert/distilbert-base-uncased")""",
        "citation": """@misc{sanh2019,
  title = {DistilBERT, a distilled version of BERT: smaller, faster, cheaper and lighter},
  author = {Victor Sanh and Lysandre Debut and Julien Chaumond and Thomas Wolf},
  year = {2019},
  eprint = {1910.01108},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/1910.01108}
}""",
    },
    "modernbert-base": {
        "model_parameters": "150M",
        "model_architecture": "Encoder-only (BERT-style) transformer trained with masked language modeling; used for embeddings and fine-tuned classification/token tasks.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/answerdotai/ModernBERT-base",
        "task_type": "fill-mask",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("fill-mask", model="answerdotai/ModernBERT-base")""",
        "citation": """@misc{warner2024,
  title = {Smarter, Better, Faster, Longer: A Modern Bidirectional Encoder for Fast, Memory Efficient, and Long Context Finetuning and Inference},
  author = {Benjamin Warner and Antoine Chaffin and Benjamin Clavié and Orion Weller and Oskar Hallström and Said Taghadouini and Alexis Gallagher and Raja Biswas and Faisal Ladhak and Tom Aarsen and Nathan Cooper and Griffin Adams and Jeremy Howard and Iacopo Poli},
  year = {2024},
  eprint = {2412.13663},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2412.13663}
}""",
    },
    "xlm-roberta-base": {
        "model_parameters": "279M",
        "model_architecture": "Encoder-only (BERT-style) transformer trained with masked language modeling; used for embeddings and fine-tuned classification/token tasks.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/FacebookAI/xlm-roberta-base",
        "task_type": "fill-mask",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("fill-mask", model="FacebookAI/xlm-roberta-base")""",
        "citation": """@misc{conneau2019,
  title = {Unsupervised Cross-lingual Representation Learning at Scale},
  author = {Alexis Conneau and Kartikay Khandelwal and Naman Goyal and Vishrav Chaudhary and Guillaume Wenzek and Francisco Guzmán and Edouard Grave and Myle Ott and Luke Zettlemoyer and Veselin Stoyanov},
  year = {2019},
  eprint = {1911.02116},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/1911.02116}
}""",
    },
    "albert-base-v2": {
        "model_parameters": "12M",
        "model_architecture": "Encoder-only (BERT-style) transformer trained with masked language modeling; used for embeddings and fine-tuned classification/token tasks.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/albert/albert-base-v2",
        "task_type": "fill-mask",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("fill-mask", model="albert/albert-base-v2")""",
        "citation": """@misc{lan2019,
  title = {ALBERT: A Lite BERT for Self-supervised Learning of Language Representations},
  author = {Zhenzhong Lan and Mingda Chen and Sebastian Goodman and Kevin Gimpel and Piyush Sharma and Radu Soricut},
  year = {2019},
  eprint = {1909.11942},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/1909.11942}
}""",
    },
}
