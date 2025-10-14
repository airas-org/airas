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
    config_yaml: str

    def to_file_dict(
        self, experiment_runs: list[ExperimentRun] | None = None
    ) -> dict[str, str]:
        files = {
            "src/train.py": self.train_py,
            "src/evaluate.py": self.evaluate_py,
            "src/preprocess.py": self.preprocess_py,
            "src/model.py": self.model_py,
            "src/main.py": self.main_py,
            "pyproject.toml": self.pyproject_toml,
            "config/config.yaml": self.config_yaml,
        }
        if experiment_runs:
            files.update(
                {
                    f"config/run/{exp_run.run_id}.yaml": exp_run.run_config
                    for exp_run in experiment_runs
                    if exp_run.run_config
                }
            )
        return files


class ExperimentEvaluation(BaseModel):
    consistency_score: Optional[int] = Field(
        None,
        description="Score (1-10) indicating consistency between experimental design and results",
    )
    consistency_feedback: Optional[str] = Field(
        None,
        description="Detailed feedback on experimental consistency and quality",
    )


class ExperimentalDesign(BaseModel):
    experiment_summary: str = Field(
        None, description="A summary of the overall experimental design"
    )
    evaluation_metrics: list[str] = Field(
        None, description="Metrics used to evaluate the experiments"
    )
    proposed_method: str = Field(
        None, description="A detailed description of the new method to be implemented"
    )
    comparative_methods: list[str] = Field(
        None, description="Existing methods selected for comparison"
    )
    models_to_use: Optional[list[str]] = Field(
        None, description="List of models to be used in the experiments"
    )
    datasets_to_use: Optional[list[str]] = Field(
        None, description="List of datasets to be used in the experiments"
    )
    hyperparameters_to_search: Optional[dict[str, str]] = Field(
        None, description="Hyperparameters to be explored in the experiments"
    )
    external_resources: Optional[ExternalResources] = Field(
        None,
        description="External resources including models, datasets, and other resources",
    )
    experiment_code: Optional[ExperimentCode] = Field(None, description="")


class ExperimentRun(BaseModel):
    run_id: str = Field(
        ...,
        description="A unique identifier for this specific experimental run (e.g., 'run-1-proposed-bert-glue-mrpc').",
    )
    method_name: str = Field(
        ...,
        description="The name of the method used in this run (e.g., 'baseline', 'proposed').",
    )
    model_name: Optional[str] = Field(
        ..., description="The name of the model used in this run."
    )
    dataset_name: Optional[str] = Field(
        ..., description="The name of the dataset used in this run."
    )
    run_config: Optional[str] = Field(
        None,
        description="Configuration for this specific run as a YAML string.",
    )
    github_repository_info: Optional[GitHubRepositoryInfo] = Field(
        None,
        description="Information about the GitHub branch where the code for this run is stored.",
    )
    results: Optional[ExperimentalResults] = Field(
        None, description="The results of this run."
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
    experiment_runs: Optional[list[ExperimentRun]] = Field(None, description="")
    experimental_analysis: Optional[ExperimentalAnalysis] = Field(None, description="")
