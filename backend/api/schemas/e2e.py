from pydantic import BaseModel

from airas.types.experimental_design import RunnerConfig
from airas.types.github import GitHubConfig
from airas.types.research_history import ResearchHistory
from airas.types.wandb import WandbConfig


class ExecuteE2ERequestBody(BaseModel):
    github_config: GitHubConfig
    research_topic: str
    runner_config: RunnerConfig
    wandb_config: WandbConfig
    is_github_repo_private: bool = False
    num_paper_search_queries: int = 1
    papers_per_query: int = 2
    hypothesis_refinement_iterations: int = 1
    num_experiment_models: int = 1
    num_experiment_datasets: int = 1
    num_comparison_methods: int = 1
    experiment_code_validation_iterations: int = 3
    paper_content_refinement_iterations: int = 2
    latex_template_name: str = "iclr2024"


class ExecuteE2EResponseBody(BaseModel):
    task_id: str
    status: str
    error: str | None = None
    research_history: ResearchHistory | None = None
