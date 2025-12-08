from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, HttpUrl

ModelSubfield = Literal[
    "transformer_decoder_based_models",
    "image_models",
    "multi_modal_models",
]

DatasetSubfield = Literal["language_model_fine_tuning_datasets", "image_datasets"]

DataModalities = Literal[
    "text", "image", "audio", "video", "tabular", "time_series", "graph", "embeddings"
]


TextTaskType = Literal["text-generation"]

ImageTaskType = Literal[
    "object-detection",
    "semantic-segmentation",
    "instance-segmentation",
    "panoptic-segmentation",
    "video-object-segmentation",
    "image-classification",
    "image-captioning",
    "image-embeddings",
    "face-detection",
    "face-verification",  # 顔認証(本人確認)
    "face-identification",  # 顔識別(誰かを特定)
    "few-shot-classification",  # Meta-learningにおける少数ショット学習タスク
    "one-shot-classification",  # Meta-learningにおける一ショット学習タスク
    "facial-expression-recognition",
    "valence-arousal-prediction",  # 感情推定（Affective Computing）における連続値回帰タスク
]

TaskType = TextTaskType | ImageTaskType


class ModelParameters(BaseModel):
    total_parameters: str
    active_parameters: str


class ModelConfig(BaseModel):
    model_parameters: ModelParameters | str
    model_architecture: str
    training_data_sources: Optional[str]
    huggingface_url: HttpUrl
    input_modalities: list[DataModalities]
    dependent_packages: list[str]
    code: str
    citation: str
    task_type: TaskType
    output_modalities: Optional[list[DataModalities]] = None
    language_distribution: Optional[str] = None
    image_size: Optional[str] = None


class DatasetConfig(BaseModel):
    description: str
    num_training_samples: int | str
    num_validation_samples: int | str
    huggingface_url: HttpUrl
    dependent_packages: list[str]
    code: str
    citation: str
    task_type: list[TaskType]
    language_distribution: Optional[str] = None
    image_size: Optional[str] = None
    sample_data: Optional[dict] = None


class ExperimentalDesign(BaseModel):
    experiment_summary: Optional[str] = Field(
        None,
        description="Overall experimental design including task definition, data handling approach, and implementation details",
    )
    runner_config: Optional[RunnerConfig] = Field(
        None, description="Computational environment specification"
    )
    evaluation_metrics: Optional[list[EvaluationMetric]] = Field(
        None,
        description="Evaluation metrics with detailed calculation methods and visualizations",
    )
    models_to_use: Optional[list[str]] = Field(
        None, description="List of models to be used in the experiments"
    )
    datasets_to_use: Optional[list[str]] = Field(
        None, description="List of datasets to be used in the experiments"
    )
    proposed_method: MethodConfig = Field(
        ..., description="Configuration for the proposed method"
    )
    comparative_methods: Optional[list[MethodConfig]] = Field(
        None, description="Configurations for baseline/comparative methods"
    )


class RunnerConfig(BaseModel):
    runner_label: str = Field(
        ..., description="Runner label used by GitHub Actions (e.g., 'ubuntu-latest')"
    )
    description: str = Field(
        ...,
        description="Machine specifications and environment details for LLM to design appropriate experiments",
    )


class EvaluationMetric(BaseModel):
    name: str = Field(..., description="Metric name")
    description: str = Field(
        ...,
        description="Detailed description including calculation method, correctness criteria, task appropriateness, and relevant visualizations",
    )


class MethodConfig(BaseModel):
    method_name: str = Field(
        ..., description="Name of the method (e.g., 'Proposed-v1', 'BERT-Baseline')"
    )
    description: str = Field(
        ..., description="Brief description of the method mechanism"
    )
    training_config: Optional[TrainingConfig] = Field(
        None, description="Training hyperparameters for this method"
    )
    optuna_config: Optional[OptunaConfig] = Field(
        None,
        description="Hyperparameter search configuration for this method (includes search spaces and trial settings)",
    )


class TrainingConfig(BaseModel):
    learning_rate: Optional[float] = Field(
        None, description="Learning rate for training"
    )
    batch_size: Optional[int] = Field(None, description="Batch size for training")
    epochs: Optional[int] = Field(None, description="Number of training epochs")
    optimizer: Optional[str] = Field(
        None, description="Optimizer (e.g., 'adam', 'adamw', 'sgd')"
    )
    warmup_steps: Optional[int] = Field(
        None, description="Number of warmup steps for learning rate scheduler"
    )
    weight_decay: Optional[float] = Field(
        None, description="Weight decay for regularization"
    )
    gradient_clip: Optional[float] = Field(
        None, description="Gradient clipping value to prevent exploding gradients"
    )
    scheduler: Optional[str] = Field(
        None, description="Learning rate scheduler (e.g., 'linear', 'cosine')"
    )
    seed: int = Field(42, description="Random seed for reproducibility")
    additional_params: Optional[str] = Field(
        None,
        description="Additional experiment-specific parameters",
    )


class OptunaConfig(BaseModel):
    enabled: bool = Field(
        default=True, description="Whether to enable Optuna optimization"
    )
    n_trials: int = Field(default=20, description="Number of Optuna trials to run")
    search_spaces: Optional[list[SearchSpace]] = Field(
        None, description="Hyperparameter search space definitions"
    )


class SearchSpace(BaseModel):
    param_name: str = Field(..., description="Parameter name to optimize")
    distribution_type: str = Field(
        ...,
        description="Distribution type: 'loguniform', 'uniform', 'int', or 'categorical'",
    )
    low: Optional[float] = Field(
        None, description="Lower bound for continuous/integer distributions"
    )
    high: Optional[float] = Field(
        None, description="Upper bound for continuous/integer distributions"
    )
    choices: Optional[list[str | int | float]] = Field(
        None, description="Choices for categorical distribution"
    )
