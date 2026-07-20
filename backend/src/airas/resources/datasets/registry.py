# Aggregates all curated dataset subfields into one lookup, mapping each
# DatasetSubfield to its registry dict. Reorganized into a category tree
# (language / vision / code / speech / multimodal) mirroring
# resources/models; the subfield API stays stable for retrieve_datasets.
from airas.resources.datasets.code.evaluation import CODE_EVALUATION_DATASETS
from airas.resources.datasets.language.evaluation import (
    LANGUAGE_MODEL_EVALUATION_DATASETS,
)
from airas.resources.datasets.language.fine_tuning import (
    LANGUAGE_MODEL_FINE_TUNING_DATASETS,
)
from airas.resources.datasets.language.nlp_tasks import (
    NATURAL_LANGUAGE_PROCESSING_DATASETS,
)
from airas.resources.datasets.language.prompt_engineering import (
    PROMPT_ENGINEERING_DATASETS,
)
from airas.resources.datasets.multimodal.vision_language import MULTIMODAL_DATASETS
from airas.resources.datasets.speech.asr import SPEECH_DATASETS
from airas.resources.datasets.vision.image import IMAGES_DATASETS

DATASETS_BY_SUBFIELD: dict[str, dict] = {
    "language_model_fine_tuning_datasets": LANGUAGE_MODEL_FINE_TUNING_DATASETS,
    "language_model_evaluation_datasets": LANGUAGE_MODEL_EVALUATION_DATASETS,
    "natural_language_processing_datasets": NATURAL_LANGUAGE_PROCESSING_DATASETS,
    "prompt_engineering_datasets": PROMPT_ENGINEERING_DATASETS,
    "code_evaluation_datasets": CODE_EVALUATION_DATASETS,
    "image_datasets": IMAGES_DATASETS,
    "speech_datasets": SPEECH_DATASETS,
    "multimodal_datasets": MULTIMODAL_DATASETS,
}
