from typing import Literal

# The subfields the curated model and dataset registries are keyed by.
ModelSubfield = Literal[
    # language
    "text_generation",
    "text_understanding",
    "sequence_to_sequence",
    "code_generation",
    "text_embedding",
    "reranking",
    "hosted_api",
    # vision
    "image_recognition",
    "image_generation",
    # multimodal / audio / time_series / science
    "vision_language",
    "speech",
    "forecasting",
    "protein",
]

DatasetSubfield = Literal[
    # language
    "instruction_tuning",
    "reasoning_evaluation",
    "nlp_tasks",
    "prompt_engineering",
    "code_evaluation",
    # vision / audio / multimodal
    "image_recognition",
    "speech",
    "vision_language",
]
