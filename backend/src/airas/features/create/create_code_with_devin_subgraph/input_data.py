from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import ExperimentalDesign, ResearchHypothesis

create_code_with_devin_subgraph_input_data = {
    "github_repository_info": GitHubRepositoryInfo(
        github_owner="auto-res2",
        repository_name="experiment_matsuzawa_retrieve_test2",
        branch_name="develop",
    ),
    "new_method": ResearchHypothesis(
        method="We propose a novel approach for automated machine learning pipeline optimization that combines reinforcement learning with neural architecture search. Our method uses a policy gradient approach to automatically select and configure data preprocessing steps, feature engineering techniques, and model architectures based on dataset characteristics and performance feedback.",
        experimental_design=ExperimentalDesign(
            experiment_details="The experiment will be conducted on multiple benchmark datasets including CIFAR-10, MNIST, and Titanic. We will compare our automated pipeline against baseline approaches including random search, grid search, and manual expert tuning. Performance will be measured using accuracy, training time, and resource utilization.",
        ),
    ),
}
