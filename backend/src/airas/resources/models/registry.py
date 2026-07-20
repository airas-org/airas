# Aggregates curated model categories into MODELS_BY_SUBFIELD, keyed by
# the shared taxonomy leaf (category). Folders are the shared domains
# (language / vision / multimodal / audio / time_series / science),
# mirroring resources/libraries and resources/datasets.
from airas.resources.models.audio.speech import SPEECH_MODELS
from airas.resources.models.language.code_generation import CODE_GENERATION_MODELS
from airas.resources.models.language.hosted_api import HOSTED_API_MODELS
from airas.resources.models.language.reranking import RERANKING_MODELS
from airas.resources.models.language.sequence_to_sequence import (
    SEQUENCE_TO_SEQUENCE_MODELS,
)
from airas.resources.models.language.text_embedding import TEXT_EMBEDDING_MODELS
from airas.resources.models.language.text_generation import TEXT_GENERATION_MODELS
from airas.resources.models.language.text_understanding import TEXT_UNDERSTANDING_MODELS
from airas.resources.models.multimodal.vision_language import VISION_LANGUAGE_MODELS
from airas.resources.models.science.protein import PROTEIN_MODELS
from airas.resources.models.time_series.forecasting import FORECASTING_MODELS
from airas.resources.models.vision.image_generation import IMAGE_GENERATION_MODELS
from airas.resources.models.vision.image_recognition import IMAGE_RECOGNITION_MODELS

MODELS_BY_SUBFIELD: dict[str, dict] = {
    "text_generation": TEXT_GENERATION_MODELS,
    "code_generation": CODE_GENERATION_MODELS,
    "text_embedding": TEXT_EMBEDDING_MODELS,
    "text_understanding": TEXT_UNDERSTANDING_MODELS,
    "sequence_to_sequence": SEQUENCE_TO_SEQUENCE_MODELS,
    "reranking": RERANKING_MODELS,
    "hosted_api": HOSTED_API_MODELS,
    "image_recognition": IMAGE_RECOGNITION_MODELS,
    "image_generation": IMAGE_GENERATION_MODELS,
    "vision_language": VISION_LANGUAGE_MODELS,
    "speech": SPEECH_MODELS,
    "forecasting": FORECASTING_MODELS,
    "protein": PROTEIN_MODELS,
}
