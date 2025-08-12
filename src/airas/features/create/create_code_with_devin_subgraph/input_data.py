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
            experiment_code="""
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import numpy as np

class AutoMLPipeline:
    def __init__(self, dataset_characteristics):
        self.dataset_chars = dataset_characteristics
        self.policy_network = self._build_policy_network()

    def _build_policy_network(self):
        # Policy network for selecting preprocessing and model configs
        return nn.Sequential(
            nn.Linear(len(self.dataset_chars), 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 32)  # Output space for decisions
        )

    def optimize_pipeline(self, train_data, val_data, episodes=100):
        best_accuracy = 0
        best_config = None

        for episode in range(episodes):
            # Sample configuration from policy
            config = self.sample_configuration()

            # Build and train model with sampled config
            model = self.build_model(config)
            accuracy = self.train_and_evaluate(model, train_data, val_data)

            # Update policy based on performance
            self.update_policy(config, accuracy)

            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_config = config

        return best_config, best_accuracy
""",
        ),
    ),
}
