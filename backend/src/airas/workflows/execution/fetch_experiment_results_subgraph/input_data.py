from airas.core.types.github import GitHubConfig

fetch_experiment_results_subgraph_input_data: dict = {
    "github_config": GitHubConfig(
        github_owner="auto-res2",
        repository_name="test",
        branch_name="main",
    ),
}
