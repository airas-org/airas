# Curated model registry (see resources/models/registry.py for the
# subfield aggregation). HuggingFace URLs and arXiv citations are verified
# on entry; add candidates via search_huggingface_hub for un-curated needs.
ENCODER_DECODER_LANGUAGE_MODELS: dict = {
    "t5-base": {
        "model_parameters": "223M",
        "model_architecture": "Encoder-decoder (sequence-to-sequence) transformer for text-to-text tasks.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/google-t5/t5-base",
        "task_type": "text2text-generation",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("text2text-generation", model="google-t5/t5-base")""",
        "citation": """@misc{raffel2019,
  title = {Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer},
  author = {Colin Raffel and Noam Shazeer and Adam Roberts and Katherine Lee and Sharan Narang and Michael Matena and Yanqi Zhou and Wei Li and Peter J. Liu},
  year = {2019},
  eprint = {1910.10683},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/1910.10683}
}""",
    },
    "flan-t5-base": {
        "model_parameters": "248M",
        "model_architecture": "Encoder-decoder (sequence-to-sequence) transformer for text-to-text tasks.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/google/flan-t5-base",
        "task_type": "text2text-generation",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("text2text-generation", model="google/flan-t5-base")""",
        "citation": """@misc{chung2022,
  title = {Scaling Instruction-Finetuned Language Models},
  author = {Hyung Won Chung and Le Hou and Shayne Longpre and Barret Zoph and Yi Tay and William Fedus and Yunxuan Li and Xuezhi Wang and Mostafa Dehghani and Siddhartha Brahma and Albert Webson and Shixiang Shane Gu and Zhuyun Dai and Mirac Suzgun and Xinyun Chen and Aakanksha Chowdhery and Alex Castro-Ros and Marie Pellat and Kevin Robinson and Dasha Valter and Sharan Narang and Gaurav Mishra and Adams Yu and Vincent Zhao and Yanping Huang and Andrew Dai and Hongkun Yu and Slav Petrov and Ed H. Chi and Jeff Dean and Jacob Devlin and Adam Roberts and Denny Zhou and Quoc V. Le and Jason Wei},
  year = {2022},
  eprint = {2210.11416},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2210.11416}
}""",
    },
    "bart-base": {
        "model_parameters": "139M",
        "model_architecture": "Encoder-decoder (sequence-to-sequence) transformer for text-to-text tasks.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/facebook/bart-base",
        "task_type": "text2text-generation",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("text2text-generation", model="facebook/bart-base")""",
        "citation": """@misc{lewis2019,
  title = {BART: Denoising Sequence-to-Sequence Pre-training for Natural Language Generation, Translation, and Comprehension},
  author = {Mike Lewis and Yinhan Liu and Naman Goyal and Marjan Ghazvininejad and Abdelrahman Mohamed and Omer Levy and Ves Stoyanov and Luke Zettlemoyer},
  year = {2019},
  eprint = {1910.13461},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/1910.13461}
}""",
    },
}
