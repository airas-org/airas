from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from airas.types.github import GitHubRepositoryInfo
from airas.types.hugging_face import HuggingFace


class ExternalResources(BaseModel):
    hugging_face: Optional[HuggingFace] = Field(
        None, description="Hugging Face models and datasets"
    )


class ExperimentCode(BaseModel):
    train_py: str
    evaluate_py: str
    preprocess_py: str
    model_py: str
    main_py: str
    pyproject_toml: str
    smoke_test_yaml: str
    full_experiment_yaml: str

    def to_file_dict(self) -> dict[str, str]:
        return {
            "src/train.py": self.train_py,
            "src/evaluate.py": self.evaluate_py,
            "src/preprocess.py": self.preprocess_py,
            "src/model.py": self.model_py,
            "src/main.py": self.main_py,
            "pyproject.toml": self.pyproject_toml,
            "config/smoke_test.yaml": self.smoke_test_yaml,
            "config/full_experiment.yaml": self.full_experiment_yaml,
        }


# TODO: Consider how to maintain the history of experimental parameters
class Experiment(BaseModel):
    experiment_id: str = Field(
        ...,
        description="A unique identifier for this major experiment (e.g., 'exp-1', 'exp-2').",
    )
    # TODO?: It might be okay to make it a class definition in the future.
    run_variations: list[str] = Field(
        ...,
        description="A definiation of variations for experiments (e.g., 'baseline', 'proposed').",
    )
    description: str = Field(
        ...,
        description="The objective or hypothesis for this experiment.",
    )
    github_repository_info: Optional[GitHubRepositoryInfo] = Field(
        None,
        description="Information about the GitHub branch where the code for this experiment is stored.",
    )
    code: Optional[ExperimentCode] = Field(
        None, description="The specific code of this experiment."
    )
    results: Optional[ExperimentalResults] = Field(
        None, description="The results of this experiment"
    )


class ExperimentalDesign(BaseModel):
    experiment_strategy: Optional[str] = Field(None, description="")
    experiments: Optional[list[Experiment]] = Field(
        None, description="List of primary experimental lines to be executed."
    )
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

    def get_experiment_by_id(self, experiment_id: str) -> Optional[Experiment]:
        return next(
            (
                experiment
                for experiment in self.experiments
                if experiment.experiment_id == experiment_id
            ),
            None,
        )


class ExperimentalResults(BaseModel):
    result: Optional[str] = Field(None, description="")
    error: Optional[str] = Field(None, description="")
    image_file_name_list: Optional[list[str]] = Field(None, description="")


class ExperimentalAnalysis(BaseModel):
    analysis_report: Optional[str] = Field(None, description="")
    # TODO: Select which experimental results to include in the paper. e.g. selected_experiment_ids: list[str]?


class ResearchHypothesis(BaseModel):
    method: str = Field(..., description="")
    experimental_design: Optional[ExperimentalDesign] = Field(None, description="")
    experimental_analysis: Optional[ExperimentalAnalysis] = Field(None, description="")
    iteration_history: Optional[list[ResearchHypothesis]] = Field(
        None, description="Previous iterations of this research hypothesis"
    )
