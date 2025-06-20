from pydantic import BaseModel, Field
from typing import Optional

class ExperimentResult(BaseModel):
    # 現在のoutput_text_data
		result: str = Field(..., description="Experimental results obtained from the standard output of the script executed by GitHub Actions.")
    # 現在のerror_text_data
		error: str = Field(..., description="Error message obtained from standard error of script executed with GitHub Actions")
		image_file_name_list: list[str] = Field(..., description="File names of graphs and figures depicting experimental results")

class ExperimentStatusInfo(BaseModel):
    iteration: int = Field(..., description="")
    push_completion: bool = Field(..., description="")
    executed_flag: bool = Field(..., description="")


class NewMethodData(BaseModel):
    new_method: str = Field(..., description="")
    verification_policy: Optional[str] = Field(..., description="")
    experimet_details: Optional[str] = Field(..., description="")
    experimet_code: Optional[str] = Field(..., description="")
    experiment_result: ExperimentResult
    experiment_status_info: ExperimentStatusInfo
