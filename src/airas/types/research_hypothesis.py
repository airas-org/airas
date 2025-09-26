from __future__ import annotations

from typing import Any, Optional

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


class ExperimentRun(BaseModel):
    run_id: str = Field(
        ...,
        description="A unique identifier for this run (e.g., 'exp-1-lr-0.01').",
    )
    parameters: dict[str, Any] = Field(..., description="The parameters for this run")
    code: Optional[ExperimentCode] = Field(
        None, description="The specific code generated to run this run."
    )
    results: Optional[ExperimentalResults] = Field(
        None, description="The results of the experimental run for this run."
    )


class Experiment(BaseModel):
    experiment_id: str = Field(
        ...,
        description="A unique identifier for this major experiment (e.g., 'exp-1', 'exp-2').",
    )
    description: str = Field(
        ..., description="The objective or hypothesis for this line of experimentation."
    )
    runs: list[ExperimentRun] = Field(
        ...,
        description="A list of parameter runs to be tested within this experiment.",
    )

    def get_run_by_id(self, run_id: str) -> Optional[ExperimentRun]:
        return next((run for run in self.runs if run.run_id == run_id), None)


class ExperimentalDesign(BaseModel):
    experiment_strategy: Optional[str] = Field(None, description="")
    experiment_details: Optional[str] = Field(
        None, description=""
    )  # TODO: # It may become unnecessary if `experiments` field exists.
    # experiments: Optional[list[Experiment]] = Field(None, description="List of primary experimental lines to be executed.")
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
    base_code: Optional[ExperimentCode] = Field(None, description="")
    experiment_code: Optional[ExperimentCode] = Field(
        None, description=""
    )  # TODO: Temporarily unified, but need to be separated for each experiment.


class ExperimentalResults(BaseModel):
    result: Optional[str] = Field(None, description="")
    error: Optional[str] = Field(None, description="")
    image_file_name_list: Optional[list[str]] = Field(None, description="")


class ExperimentalAnalysis(BaseModel):
    analysis_report: Optional[str] = Field(None, description="")
    # TODO: Select which experimental results to include in the paper.


class ResearchHypothesis(BaseModel):
    method: str = Field(..., description="")
    experimental_design: Optional[ExperimentalDesign] = Field(None, description="")
    experimental_results: Optional[ExperimentalResults] = Field(
        None, description=""
    )  # TODO: # It may become unnecessary if `experiments` field exists.
    experimental_analysis: Optional[ExperimentalAnalysis] = Field(None, description="")
    iteration_history: Optional[list[ResearchHypothesis]] = Field(
        None, description="Previous iterations of this research hypothesis"
    )
