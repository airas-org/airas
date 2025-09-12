from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class HuggingFaceSibling(BaseModel):
    rfilename: str = Field(..., description="Relative filename in the repository")
    size: Optional[int] = Field(None, description="File size in bytes")
    blob_id: Optional[str] = Field(None, description="Blob ID for the file")
    lfs: Optional[dict[str, Any]] = Field(
        None, description="LFS information if applicable"
    )


class HuggingFaceCardData(BaseModel):
    license: Optional[str | list[str]] = Field(
        None, description="License of the resource"
    )
    language: Optional[str | list[str]] = Field(
        default_factory=list, description="Supported languages"
    )
    library_name: Optional[str] = Field(
        None, description="Associated library (transformers, datasets, etc.)"
    )
    pipeline_tag: Optional[str] = Field(None, description="Pipeline task tag")
    tags: Optional[str | list[str]] = Field(
        default_factory=list, description="General tags"
    )
    datasets: Optional[str | list[str]] = Field(
        default_factory=list, description="Associated datasets"
    )

    model_type: Optional[str] = Field(
        None, description="Type of the model (bert, gpt2, etc.)"
    )
    base_model: Optional[str | list[str]] = Field(
        None, description="Base model if this is a fine-tuned model"
    )

    task_categories: Optional[str | list[str]] = Field(
        default_factory=list, description="Task categories for datasets"
    )
    size_categories: Optional[str | list[str]] = Field(
        default_factory=list, description="Size categories for datasets"
    )

    metrics: Optional[str | list[str]] = Field(
        default_factory=list, description="Evaluation metrics"
    )
    widget: Optional[list[dict[str, Any]]] = Field(
        default_factory=list, description="Widget examples"
    )


class HuggingFaceResource(BaseModel):
    id: str = Field(..., description="Unique identifier (namespace/repo-name)")
    author: Optional[str] = Field(None, description="Author name")
    sha: Optional[str] = Field(None, description="Git SHA of the latest commit")

    created_at: Optional[datetime] = Field(
        None, description="Creation timestamp", alias="createdAt"
    )
    last_modified: Optional[datetime] = Field(
        None, description="Last modification timestamp", alias="lastModified"
    )
    private: bool = Field(False, description="Whether the repository is private")
    gated: str | bool = Field(
        False, description="Whether the resource requires access approval"
    )
    disabled: bool = Field(False, description="Whether the resource is disabled")

    downloads: int = Field(0, description="Number of downloads")
    likes: int = Field(0, description="Number of likes")

    siblings: list[HuggingFaceSibling] = Field(
        default_factory=list, description="Files in the repository"
    )
    card_data: Optional[HuggingFaceCardData] = Field(
        None, description="Structured card metadata", alias="cardData"
    )

    tags: str | list[str] = Field(default_factory=list, description="Repository tags")
    pipeline_tag: Optional[str] = Field(
        None, description="Primary pipeline task", alias="pipeline-tag"
    )
    library_name: Optional[str] = Field(None, description="Primary library name")

    readme: str = Field(
        "",
        description="Enriched by a separate README fetch; not part of the main API response",
    )
    model_index: Optional[list[dict[str, Any]]] = Field(
        None, description="Model index information", alias="model-index"
    )

    widget_data: Optional[list[dict[str, Any]]] = Field(
        None, description="Widget examples data", alias="widgetData"
    )
    config: Optional[dict[str, Any]] = Field(
        None, description="Model configuration information"
    )
    transformers_info: Optional[dict[str, Any]] = Field(
        None,
        description="Transformers library specific information",
        alias="transformersInfo",
    )
    spaces: Optional[list[str]] = Field(None, description="Related Hugging Face Spaces")
    safetensors: Optional[dict[str, Any]] = Field(
        None, description="Safetensors metadata"
    )
    used_storage: Optional[int] = Field(
        None, description="Used storage in bytes", alias="usedStorage"
    )

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class HuggingFace(BaseModel):
    models: list[HuggingFaceResource] = Field(
        default_factory=list, description="Found models"
    )
    datasets: list[HuggingFaceResource] = Field(
        default_factory=list, description="Found datasets"
    )
