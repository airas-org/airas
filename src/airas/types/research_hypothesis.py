from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from airas.types.hugging_face import HuggingFace


class ExternalResources(BaseModel):
    hugging_face: Optional[HuggingFace] = Field(
        None, description="Hugging Face models and datasets"
    )


class ExperimentCode(BaseModel):
    train_py: str
    evaluate_py: str
    preprocess_py: str
    main_py: str
    pyproject_toml: str
    smoke_test_yaml: str
    full_experiment_yaml: str

    def to_file_dict(self) -> dict[str, str]:
        return {
            "src/train.py": self.train_py,
            "src/evaluate.py": self.evaluate_py,
            "src/preprocess.py": self.preprocess_py,
            "src/main.py": self.main_py,
            "pyproject.toml": self.pyproject_toml,
            "config/smoke_test.yaml": self.smoke_test_yaml,
            "config/full_experiment.yaml": self.full_experiment_yaml,
        }


class ExperimentalDesign(BaseModel):
    experiment_strategy: Optional[str] = Field(None, description="")
    experiment_details: Optional[str] = Field(None, description="")
    expected_models: Optional[list[str]] = Field(
        None, description="List of expected models to be used in the experiment"
    )
    expected_datasets: Optional[list[str]] = Field(
        None, description="List of expected datasets to be used in the experiment"
    )
    external_resources: Optional[ExternalResources] = Field(
        None,
        description="External resources including models, datasets, and other resources",
    )
    experiment_code: Optional[ExperimentCode] = Field(None, description="")


class ExperimentalResults(BaseModel):
    result: Optional[str] = Field(None, description="")
    error: Optional[str] = Field(None, description="")
    image_file_name_list: Optional[list[str]] = Field(None, description="")
    notes: Optional[str] = Field(None, description="")  # 外部で持たなくていい気がする


class ExperimentalAnalysis(BaseModel):
    analysis_report: Optional[str] = Field(None, description="")


class ResearchHypothesis(BaseModel):
    method: str = Field(..., description="")
    experimental_design: Optional[ExperimentalDesign] = Field(None, description="")
    experimental_results: Optional[ExperimentalResults] = Field(None, description="")
    experimental_analysis: Optional[ExperimentalAnalysis] = Field(None, description="")
    iteration_history: Optional[list[ResearchHypothesis]] = Field(
        None, description="Previous iterations of this research hypothesis"
    )
