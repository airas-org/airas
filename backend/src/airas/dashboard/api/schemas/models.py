from pydantic import BaseModel

from airas.core.types.experimental_design import ModelConfig, ModelSubfield


class RetrieveModelsSubgraphRequestBody(BaseModel):
    model_subfield: ModelSubfield


class RetrieveModelsSubgraphResponseBody(BaseModel):
    models_dict: dict[str, ModelConfig]
    execution_time: dict[str, list[float]]
