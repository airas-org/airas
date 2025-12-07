from airas.data.models.transformer_decoder_based_models import (
    TRANSFORMER_DECODER_BASED_MODELS_LIST,
)
from airas.types.experimental_design import ModelSubfield


def retrieve_models(subfields: ModelSubfield) -> dict:
    if subfields == "transformer_decoder_based_models":
        return TRANSFORMER_DECODER_BASED_MODELS_LIST
