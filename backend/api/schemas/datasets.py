from pydantic import BaseModel

from airas.types.experimental_design import DatasetSubfield


class RetrieveDatasetsSubgraphRequestBody(BaseModel):
    dataset_subfield: DatasetSubfield


class RetrieveDatasetsSubgraphResponseBody(BaseModel):
    datasets_dict: dict
    execution_time: dict[str, list[float]]
