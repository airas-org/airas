# Curated model registry (see resources/models/registry.py for the
# subfield aggregation). HuggingFace URLs and arXiv citations are verified
# on entry; add candidates via search_huggingface_hub for un-curated needs.
SPEECH_MODELS: dict = {
    "whisper-large-v3": {
        "model_parameters": "1.5B",
        "model_architecture": "Speech model for automatic speech recognition.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/openai/whisper-large-v3",
        "task_type": "automatic-speech-recognition",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("automatic-speech-recognition", model="openai/whisper-large-v3")""",
        "citation": """@misc{radford2022,
  title = {Robust Speech Recognition via Large-Scale Weak Supervision},
  author = {Alec Radford and Jong Wook Kim and Tao Xu and Greg Brockman and Christine McLeavey and Ilya Sutskever},
  year = {2022},
  eprint = {2212.04356},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2212.04356}
}""",
    },
    "wav2vec2-base-960h": {
        "model_parameters": "94M",
        "model_architecture": "Speech model for automatic speech recognition.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/facebook/wav2vec2-base-960h",
        "task_type": "automatic-speech-recognition",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("automatic-speech-recognition", model="facebook/wav2vec2-base-960h")""",
        "citation": """@misc{baevski2020,
  title = {wav2vec 2.0: A Framework for Self-Supervised Learning of Speech Representations},
  author = {Alexei Baevski and Henry Zhou and Abdelrahman Mohamed and Michael Auli},
  year = {2020},
  eprint = {2006.11477},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2006.11477}
}""",
    },
    "hubert-base-ls960": {
        "model_parameters": "Unknown",
        "model_architecture": "Speech model for automatic speech recognition.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/facebook/hubert-base-ls960",
        "task_type": "automatic-speech-recognition",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("automatic-speech-recognition", model="facebook/hubert-base-ls960")""",
        "citation": """@misc{hsu2021,
  title = {HuBERT: Self-Supervised Speech Representation Learning by Masked Prediction of Hidden Units},
  author = {Wei-Ning Hsu and Benjamin Bolte and Yao-Hung Hubert Tsai and Kushal Lakhotia and Ruslan Salakhutdinov and Abdelrahman Mohamed},
  year = {2021},
  eprint = {2106.07447},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2106.07447}
}""",
    },
}
