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
    "whisper-small": {
        "model_parameters": "242M",
        "model_architecture": "Speech/audio model.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/openai/whisper-small",
        "task_type": "automatic-speech-recognition",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("automatic-speech-recognition", model="openai/whisper-small")""",
        "citation": """@misc{radford2022,
  title = {Robust Speech Recognition via Large-Scale Weak Supervision},
  author = {Alec Radford and Jong Wook Kim and Tao Xu and Greg Brockman and Christine McLeavey and Ilya Sutskever},
  year = {2022},
  eprint = {2212.04356},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2212.04356}
}""",
    },
    "mms-1b-all": {
        "model_parameters": "965M",
        "model_architecture": "Speech/audio model.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/facebook/mms-1b-all",
        "task_type": "automatic-speech-recognition",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("automatic-speech-recognition", model="facebook/mms-1b-all")""",
        "citation": """@misc{pratap2023,
  title = {Scaling Speech Technology to 1,000+ Languages},
  author = {Vineel Pratap and Andros Tjandra and Bowen Shi and Paden Tomasello and Arun Babu and Sayani Kundu and Ali Elkahky and Zhaoheng Ni and Apoorv Vyas and Maryam Fazel-Zarandi and Alexei Baevski and Yossi Adi and Xiaohui Zhang and Wei-Ning Hsu and Alexis Conneau and Michael Auli},
  year = {2023},
  eprint = {2305.13516},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2305.13516}
}""",
    },
    "speecht5-tts": {
        "model_parameters": "Unknown",
        "model_architecture": "Speech/audio model.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/microsoft/speecht5_tts",
        "task_type": "text-to-speech",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("text-to-speech", model="microsoft/speecht5_tts")""",
        "citation": """@misc{ao2021,
  title = {SpeechT5: Unified-Modal Encoder-Decoder Pre-Training for Spoken Language Processing},
  author = {Junyi Ao and Rui Wang and Long Zhou and Chengyi Wang and Shuo Ren and Yu Wu and Shujie Liu and Tom Ko and Qing Li and Yu Zhang and Zhihua Wei and Yao Qian and Jinyu Li and Furu Wei},
  year = {2021},
  eprint = {2110.07205},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2110.07205}
}""",
    },
    "musicgen-small": {
        "model_parameters": "591M",
        "model_architecture": "Speech/audio model.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/facebook/musicgen-small",
        "task_type": "text-to-audio",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("text-to-audio", model="facebook/musicgen-small")""",
        "citation": """@misc{copet2023,
  title = {Simple and Controllable Music Generation},
  author = {Jade Copet and Felix Kreuk and Itai Gat and Tal Remez and David Kant and Gabriel Synnaeve and Yossi Adi and Alexandre Défossez},
  year = {2023},
  eprint = {2306.05284},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2306.05284}
}""",
    },
}
