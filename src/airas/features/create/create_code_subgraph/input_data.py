from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import ExperimentalDesign, ResearchHypothesis

dummy_experimental_design = ExperimentalDesign(
    experiment_strategy="Test strategy for validation",
    experiment_details="Simple test details for validation",
    expected_models=["test-model"],
    expected_datasets=["test-dataset"],
)

dummy_research_hypothesis = ResearchHypothesis(
    method="Simple test method for validation",
    experimental_design=dummy_experimental_design,
)

dummy_github_repo = GitHubRepositoryInfo(
    github_owner="auto-res2",
    repository_name="experiment_matsuzawa_20250911",
    branch_name="research-20250911-160618-003",
)

create_code_subgraph_input_data = {
    "github_repository_info": dummy_github_repo,
    "new_method": dummy_research_hypothesis,
    "experiment_iteration": 1,
}
