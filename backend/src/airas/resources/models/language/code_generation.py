# Curated model registry — language / code_generation. Part of the shared
# domain>category taxonomy across resources/{libraries,models,datasets}.
# HuggingFace URLs and arXiv citations are verified on entry; use
# search_huggingface_hub for un-curated needs.
CODE_GENERATION_MODELS: dict = {
    "starcoder2-7b": {
        "description": "",
        "model_parameters": "7.2B",
        "model_architecture": "Decoder-only transformer specialized for code generation.",
        "domain": "language",
        "category": "code_generation",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/bigcode/starcoder2-7b",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("text-generation", model="bigcode/starcoder2-7b")""",
        "citation": """@misc{lozhkov2024,
  title = {StarCoder 2 and The Stack v2: The Next Generation},
  author = {Anton Lozhkov and Raymond Li and Loubna Ben Allal and Federico Cassano and Joel Lamy-Poirier and Nouamane Tazi and Ao Tang and Dmytro Pykhtar and Jiawei Liu and Yuxiang Wei and Tianyang Liu and Max Tian and Denis Kocetkov and Arthur Zucker and Younes Belkada and Zijian Wang and Qian Liu and Dmitry Abulkhanov and Indraneil Paul and Zhuang Li and Wen-Ding Li and Megan Risdal and Jia Li and Jian Zhu and Terry Yue Zhuo and Evgenii Zheltonozhskii and Nii Osae Osae Dade and Wenhao Yu and Lucas Krauß and Naman Jain and Yixuan Su and Xuanli He and Manan Dey and Edoardo Abati and Yekun Chai and Niklas Muennighoff and Xiangru Tang and Muhtasham Oblokulov and Christopher Akiki and Marc Marone and Chenghao Mou and Mayank Mishra and Alex Gu and Binyuan Hui and Tri Dao and Armel Zebaze and Olivier Dehaene and Nicolas Patry and Canwen Xu and Julian McAuley and Han Hu and Torsten Scholak and Sebastien Paquet and Jennifer Robinson and Carolyn Jane Anderson and Nicolas Chapados and Mostofa Patwary and Nima Tajbakhsh and Yacine Jernite and Carlos Muñoz Ferrandis and Lingming Zhang and Sean Hughes and Thomas Wolf and Arjun Guha and Leandro von Werra and Harm de Vries},
  year = {2024},
  eprint = {2402.19173},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2402.19173}
}""",
        "training_data_sources": "",
    },
    "deepseek-coder-6.7b": {
        "description": "",
        "model_parameters": "6.7B",
        "model_architecture": "Decoder-only transformer specialized for code generation.",
        "domain": "language",
        "category": "code_generation",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/deepseek-ai/deepseek-coder-6.7b-base",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("text-generation", model="deepseek-ai/deepseek-coder-6.7b-base")""",
        "citation": """@misc{guo2024,
  title = {DeepSeek-Coder: When the Large Language Model Meets Programming -- The Rise of Code Intelligence},
  author = {Daya Guo and Qihao Zhu and Dejian Yang and Zhenda Xie and Kai Dong and Wentao Zhang and Guanting Chen and Xiao Bi and Y. Wu and Y. K. Li and Fuli Luo and Yingfei Xiong and Wenfeng Liang},
  year = {2024},
  eprint = {2401.14196},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2401.14196}
}""",
        "training_data_sources": "",
    },
    "codegen-2b": {
        "description": "",
        "model_parameters": "Unknown",
        "model_architecture": "Decoder-only transformer specialized for code generation.",
        "domain": "language",
        "category": "code_generation",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/Salesforce/codegen-2B-mono",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("text-generation", model="Salesforce/codegen-2B-mono")""",
        "citation": """@misc{nijkamp2022,
  title = {CodeGen: An Open Large Language Model for Code with Multi-Turn Program Synthesis},
  author = {Erik Nijkamp and Bo Pang and Hiroaki Hayashi and Lifu Tu and Huan Wang and Yingbo Zhou and Silvio Savarese and Caiming Xiong},
  year = {2022},
  eprint = {2203.13474},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2203.13474}
}""",
        "training_data_sources": "",
    },
}
