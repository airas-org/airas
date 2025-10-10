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


class ExperimentEvaluation(BaseModel):
    consistency_score: Optional[int] = Field(
        None,
        description="Score (1-10) indicating consistency between experimental design and results",
    )
    consistency_feedback: Optional[str] = Field(
        None,
        description="Detailed feedback on experimental consistency and quality",
    )


class HyperparameterSearchSpace(BaseModel): ...


class ExperimentRun(BaseModel):
    run_id: str = Field(
        ...,
        description="A unique identifier for this specific experimental run (e.g., 'run-1-proposed-bert-glue-mrpc').",
    )
    method_name: Optional[str] = Field(
        ...,
        description="The name of the method used in this run (e.g., 'baseline', 'proposed').",
    )
    model_name: Optional[str] = Field(
        ..., description="The name of the model used in this run."
    )
    dataset_name: Optional[str] = Field(
        ..., description="The name of the dataset used in this run."
    )
    hyperparameter_search_space: Optional[dict[str, str]] = Field(
        ...,
        description="Defines the hyperparameter search space for this specific run.",
    )
    github_repository_info: Optional[GitHubRepositoryInfo] = Field(
        None,
        description="Information about the GitHub branch where the code for this run is stored.",
    )
    results: Optional[ExperimentalResults] = Field(
        None, description="The results of this run."
    )
    evaluation: Optional[ExperimentEvaluation] = Field(
        None,
        description="Evaluation of this run's consistency and suitability for the paper.",
    )
    # TODO: code? When code modifications by Claude Code occur, is it necessary to have them?


class ExperimentalDesign(BaseModel):
    experiment_summary: Optional[str] = Field(
        None, description="A summary of the overall experimental design"
    )
    evaluation_metrics: Optional[list[str]] = Field(
        None, description="Metrics used to evaluate the experiments"
    )
    models_to_use: Optional[list[str]] = Field(
        None, description="List of models to be used in the experiments"
    )
    datasets_to_use: Optional[list[str]] = Field(
        None, description="List of datasets to be used in the experiments"
    )
    proposed_method: Optional[str] = Field(
        None, description="A detailed description of the new method to be implemented"
    )
    comparative_methods: Optional[list[str]] = Field(
        None, description="Existing methods selected for comparison"
    )
    hyperparameters_to_search: Optional[list[str]] = Field(
        None, description="Hyperparameters to be explored in the experiments"
    )
    external_resources: Optional[ExternalResources] = Field(
        None,
        description="External resources including models, datasets, and other resources",
    )
    base_code: Optional[ExperimentCode] = Field(None, description="")
    experiment_runs: Optional[list[ExperimentRun]] = Field(
        None, description="A list of all individual experimental runs"
    )

    def get_experiment_run_by_id(self, run_id: str) -> Optional[ExperimentRun]:
        return next(
            (run for run in self.experiment_runs if run.run_id == run_id),
            None,
        )


class ExperimentalResults(BaseModel):
    result: Optional[str] = Field(None, description="")
    error: Optional[str] = Field(None, description="")
    image_file_name_list: Optional[list[str]] = Field(None, description="")
    # TODO: wandb?


class ExperimentalAnalysis(BaseModel):
    analysis_report: Optional[str] = Field(None, description="")


class ResearchHypothesis(BaseModel):
    method: str = Field(..., description="")
    experimental_design: Optional[ExperimentalDesign] = Field(None, description="")
    experimental_analysis: Optional[ExperimentalAnalysis] = Field(None, description="")
    # iteration_history: Optional[list[ResearchHypothesis]] = Field(
    #     None, description="Previous iterations of this research hypothesis"
    # )
