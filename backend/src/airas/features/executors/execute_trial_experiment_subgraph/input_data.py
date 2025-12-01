from airas.types.github import GitHubConfig

execute_trial_experiment_subgraph_input_data: dict = {
    "github_config": GitHubConfig(
        github_owner="auto-res2",
        repository_name="test",
        branch_name="main",
    ),
}
