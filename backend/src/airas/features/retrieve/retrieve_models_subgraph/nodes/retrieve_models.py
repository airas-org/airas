from airas.data.models.transformer_decoder_based_models import (
    TRANSFORMER_DECODER_BASED_MODELS_LIST,
)
from airas.types.experimental_design import ModelSubfield


def retrieve_models(model_subfield: ModelSubfield) -> dict:
    if model_subfield == "transformer_decoder_based_models":
        return TRANSFORMER_DECODER_BASED_MODELS_LIST
