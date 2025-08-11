from typing import Optional

from pydantic import BaseModel, Field


class ExperimentalDesign(BaseModel):
    experiment_strategy: Optional[str] = Field(None, description="")
    experiment_details: Optional[str] = Field(None, description="")
    experiment_code: Optional[str] = Field(
        None, description=""
    )  # 実施に実験するコードではない、コードの案


class ExperimentalInformation(BaseModel):
    result: Optional[str] = Field(None, description="")
    error: Optional[str] = Field(None, description="")
    image_file_name_list: Optional[list[str]] = Field(None, description="")
    notes: Optional[str] = Field(None, description="")  # 外部で持たなくていい気がする


class ExperimentMetaInfo(BaseModel):
    iteration: Optional[int] = Field(None, description="")  # 今のexperiment_iteration
    push_completion: Optional[bool] = Field(None, description="")
    executed_flag: Optional[bool] = Field(None, description="")


class ExperimentalAnalysis(BaseModel):
    analysis_report: Optional[str] = Field(None, description="")


class ResearchHypothesis(BaseModel):
    method: str = Field(..., description="")
    experimental_design: Optional[ExperimentalDesign] = Field(None, description="")
    experimental_information: Optional[ExperimentalInformation] = Field(
        None, description=""
    )
    experimental_meta_info: Optional[ExperimentMetaInfo] = Field(None, description="")
    experimental_analysis: Optional[ExperimentalAnalysis] = Field(None, description="")
