from airas.core.types.experimental_design import ModelSubfield
from airas.resources.models.image_model import IMAGE_MODELS
from airas.resources.models.multi_modal_model import MULTI_MODAL_MODELS
from airas.resources.models.transformer_decoder_based_models import (
    TRANSFORMER_DECODER_BASED_MODELS,
)


def retrieve_models(model_subfield: ModelSubfield):
    if model_subfield == "transformer_decoder_based_models":
        return TRANSFORMER_DECODER_BASED_MODELS
    elif model_subfield == "image_models":
        return IMAGE_MODELS
    elif model_subfield == "multi_modal_models":
        return MULTI_MODAL_MODELS
