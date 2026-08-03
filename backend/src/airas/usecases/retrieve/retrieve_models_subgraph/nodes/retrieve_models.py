from airas.core.types.experimental_design import ModelSubfield
from airas.resources.models.registry import MODELS_BY_SUBFIELD


def retrieve_models(model_subfield: ModelSubfield):
    return MODELS_BY_SUBFIELD.get(model_subfield, {})
