from pydantic import BaseModel

from airas.types.experimental_design import ModelSubfield


class RetrieveModelsSubgraphRequestBody(BaseModel):
    model_subfield: ModelSubfield


class RetrieveModelsSubgraphResponseBody(BaseModel):
    models_dict: dict
    execution_time: dict[str, list[float]]
