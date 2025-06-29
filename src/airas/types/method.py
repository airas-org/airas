from typing import Optional

from pydantic import BaseModel, Field


class BaseMethodData(BaseModel):
    method: str = Field(..., description="")


class ExperimentResult(BaseModel):
    result: Optional[str] = Field(None, description="")
    error: Optional[str] = Field(None, description="")
    image_file_name_list: Optional[list[str]] = Field(None, description="")


class ExperimentMetaInfo(BaseModel):
    iteration: Optional[int] = Field(None, description="")  # 今のexperiment_iteration
    push_completion: Optional[bool] = Field(None, description="")
    executed_flag: Optional[bool] = Field(None, description="")


class MLMethodData(BaseMethodData):
    verification_policy: Optional[str] = Field(None, description="")
    experiment_details: Optional[str] = Field(None, description="")
    experiment_code: Optional[str] = Field(None, description="")
    experiment_result: Optional[ExperimentResult] = Field(None, description="")
    experiment_meta_info: Optional[ExperimentMetaInfo] = Field(None, description="")
