from pydantic import BaseModel

from airas.types.experimental_design import RunnerConfig
from airas.types.github import GitHubConfig
from airas.types.research_history import ResearchHistory
from airas.types.wandb import WandbConfig


class ExecuteE2ERequestBody(BaseModel):
    github_config: GitHubConfig
    queries: list[str]
    runner_config: RunnerConfig
    wandb_config: WandbConfig
    is_private: bool = False
    max_results_per_query: int = 5
    refinement_rounds: int = 1
    num_models_to_use: int = 1
    num_datasets_to_use: int = 1
    num_comparative_methods: int = 0
    max_code_validations: int = 3
    writing_refinement_rounds: int = 2
    latex_template_name: str = "iclr2024"


class ExecuteE2EResponseBody(BaseModel):
    task_id: str
    status: str
    error: str | None = None
    research_history: ResearchHistory | None = None
