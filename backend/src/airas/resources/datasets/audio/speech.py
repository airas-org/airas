# Curated dataset registry — audio / speech. Part of the shared
# domain>category taxonomy across resources/{libraries,models,datasets}.
# HuggingFace dataset IDs and arXiv citations are verified on entry;
# use search_huggingface_hub for un-curated needs.
SPEECH_DATASETS: dict = {
    "librispeech_asr": {
        "description": "Dataset Card for librispeech_asr Dataset Summary LibriSpeech is a corpus of approximately 1000 hours of 16kHz read English speech, prepared by Vassil Panayotov with the assistance of Daniel Povey. The data is derived from read audiobooks from the LibriVox project, and has been ca",
        "domain": "audio",
        "category": "speech",
        "task_type": "automatic-speech-recognition",
        "huggingface_url": "https://huggingface.co/datasets/openslr/librispeech_asr",
        "dependent_packages": ["datasets"],
        "code": """from datasets import load_dataset
ds = load_dataset("openslr/librispeech_asr")""",
        "citation": "",
    },
    "common_voice_17": {
        "description": "Effective October 2025, Mozilla Common Voice datasets are now exclusively available through Mozilla Data Collective. You can learn more about this change here.",
        "domain": "audio",
        "category": "speech",
        "task_type": "automatic-speech-recognition",
        "huggingface_url": "https://huggingface.co/datasets/mozilla-foundation/common_voice_17_0",
        "dependent_packages": ["datasets"],
        "code": """from datasets import load_dataset
ds = load_dataset("mozilla-foundation/common_voice_17_0")""",
        "citation": """@misc{ardila2019,
  title = {Common Voice: A Massively-Multilingual Speech Corpus},
  author = {Rosana Ardila and Megan Branson and Kelly Davis and Michael Henretty and Michael Kohler and Josh Meyer and Reuben Morais and Lindsay Saunders and Francis M. Tyers and Gregor Weber},
  year = {2019},
  eprint = {1912.06670},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/1912.06670}
}""",
    },
}
