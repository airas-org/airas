from pydantic import BaseModel, Field


class WandbInfo(BaseModel):
    entity: str = Field(..., description="Wandb entity (username or team name)")
    project: str = Field(..., description="Wandb project name")
    run_ids: list[str] | None = Field(
        default=None,
        description="List of Wandb run IDs (optional, can be retrieved from metadata)",
    )
