# Aggregates all curated model subfields into one lookup, mapping each
# ModelSubfield to its registry dict. Reorganized into a category tree
# (language / vision / multimodal / speech / api) mirroring
# resources/libraries; the subfield API stays stable for retrieve_models.
from airas.resources.models.api.llm import LLM_API_MODELS
from airas.resources.models.language.code import CODE_GENERATION_MODELS
from airas.resources.models.language.decoder import (
    TRANSFORMER_DECODER_BASED_MODELS,
)
from airas.resources.models.language.embedding import TEXT_EMBEDDING_MODELS
from airas.resources.models.language.encoder import ENCODER_LANGUAGE_MODELS
from airas.resources.models.language.encoder_decoder import (
    ENCODER_DECODER_LANGUAGE_MODELS,
)
from airas.resources.models.multimodal.vision_language import MULTI_MODAL_MODELS
from airas.resources.models.speech.recognition import SPEECH_MODELS
from airas.resources.models.vision.generative import IMAGE_GENERATIVE_MODELS
from airas.resources.models.vision.recognition import IMAGE_MODELS

MODELS_BY_SUBFIELD: dict[str, dict] = {
    "transformer_decoder_based_models": TRANSFORMER_DECODER_BASED_MODELS,
    "code_generation_models": CODE_GENERATION_MODELS,
    "text_embedding_models": TEXT_EMBEDDING_MODELS,
    "encoder_language_models": ENCODER_LANGUAGE_MODELS,
    "encoder_decoder_language_models": ENCODER_DECODER_LANGUAGE_MODELS,
    "image_models": IMAGE_MODELS,
    "image_generative_models": IMAGE_GENERATIVE_MODELS,
    "multi_modal_models": MULTI_MODAL_MODELS,
    "speech_models": SPEECH_MODELS,
    "llm_api_models": LLM_API_MODELS,
}
