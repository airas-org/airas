# Aggregates curated dataset categories into DATASETS_BY_SUBFIELD, keyed
# by the shared taxonomy leaf (category). Folders are the shared domains
# (language / vision / audio / multimodal), mirroring resources/models
# and resources/libraries.
from airas.resources.datasets.audio.speech import SPEECH_DATASETS
from airas.resources.datasets.language.code_evaluation import CODE_EVALUATION_DATASETS
from airas.resources.datasets.language.instruction_tuning import (
    INSTRUCTION_TUNING_DATASETS,
)
from airas.resources.datasets.language.nlp_tasks import NLP_TASKS_DATASETS
from airas.resources.datasets.language.prompt_engineering import (
    PROMPT_ENGINEERING_DATASETS,
)
from airas.resources.datasets.language.reasoning_evaluation import (
    REASONING_EVALUATION_DATASETS,
)
from airas.resources.datasets.multimodal.vision_language import VISION_LANGUAGE_DATASETS
from airas.resources.datasets.vision.image_recognition import IMAGE_RECOGNITION_DATASETS

DATASETS_BY_SUBFIELD: dict[str, dict] = {
    "instruction_tuning": INSTRUCTION_TUNING_DATASETS,
    "reasoning_evaluation": REASONING_EVALUATION_DATASETS,
    "nlp_tasks": NLP_TASKS_DATASETS,
    "prompt_engineering": PROMPT_ENGINEERING_DATASETS,
    "code_evaluation": CODE_EVALUATION_DATASETS,
    "image_recognition": IMAGE_RECOGNITION_DATASETS,
    "speech": SPEECH_DATASETS,
    "vision_language": VISION_LANGUAGE_DATASETS,
}
