from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator

CloudProvider = Literal["aws", "gcp"]


class StaticRunnerConfig(BaseModel):
    type: Literal["static"] = "static"
    runner_label: list[str] = Field(
        default_factory=lambda: ["ubuntu-latest"],
        description="Runner labels used by GitHub Actions (e.g., ['ubuntu-latest'] or ['self-hosted', 'gpu-runner'])",
    )

    @field_validator("runner_label")
    @classmethod
    def labels_not_empty(cls, v: list[str]) -> list[str]:
        filtered = [label for label in v if label.strip()]
        if not filtered:
            raise ValueError("runner_label must contain at least one non-empty label")
        return filtered


class EphemeralCloudRunnerConfig(BaseModel):
    type: Literal["ephemeral_cloud"] = "ephemeral_cloud"
    cloud_provider: CloudProvider = Field(
        default="aws",
        description="Cloud provider ('aws' or 'gcp')",
    )
    gpu_instance_type: str = Field(
        default="g4dn.xlarge",
        description="Instance type (e.g., 'g4dn.xlarge' for AWS, 'n1-standard-4' for GCP)",
    )
    max_instance_hours: str = Field(
        default="120",
        description="Max instance lifetime in hours (safety net for orphaned instances)",
    )


ExperimentRunnerConfig = Annotated[
    StaticRunnerConfig | EphemeralCloudRunnerConfig,
    Field(discriminator="type"),
]
