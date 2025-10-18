from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import (
    ResearchHypothesis,
)

create_experimental_design_subgraph_input_data = {
    "new_method": ResearchHypothesis(
        method="Adaptive Curvature Momentum (ACM) Optimizer for improved convergence in deep learning",
    ),
    "github_repository_info": GitHubRepositoryInfo(
        github_owner="auto-res2",
        repository_name="experiment_matsuzawa_251006",
        branch_name="develop",
    ),
}
