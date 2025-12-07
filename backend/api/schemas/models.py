from pydantic import BaseModel

from airas.types.experimental_design import Subfield


class RetrieveModelsSubgraphRequestBody(BaseModel):
    subfields: Subfield


class RetrieveModelsSubgraphResponseBody(BaseModel):
    models_dict: dict
    execution_time: dict[str, list[float]]
