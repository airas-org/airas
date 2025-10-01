from airas.types.research_hypothesis import (
    ExperimentalDesign,
    ExperimentalResults,
    ExperimentCode,
    ResearchHypothesis,
)

create_experimental_design_subgraph_input_data = {
    "new_method": ResearchHypothesis(
        method="Adaptive Curvature Momentum (ACM) Optimizer for improved convergence in deep learning",
        # Current experimental_design will be None after prepare_iteration_history
        experimental_design=ExperimentalDesign(
            experiment_strategy="Compare ACM against Adam/SGD on ResNet-18 using CIFAR-10",
            experiment_details="Train for 100 epochs, 3 seeds, track loss/accuracy curves",
            experiment_code=ExperimentCode(
                train_py="import torch\nclass ACMOptimizer(torch.optim.Optimizer):\n    pass\n",
                evaluate_py="def evaluate_model(model, loader):\n    pass\n",
                preprocess_py="def load_cifar10():\n    pass\n",
                model_py="import torch.nn as nn\nclass ResNet18(nn.Module):\n    pass\n",
                main_py="if __name__ == '__main__':\n    main()\n",
                pyproject_toml="[tool.poetry]\nname = 'acm-experiment'\n",
                smoke_test_yaml="epochs: 1\nseeds: 1\n",
                full_experiment_yaml="epochs: 100\nseeds: 3\n",
            ),
        ),
        experimental_results=ExperimentalResults(
            result="ACM achieved 85% accuracy vs Adam 82%",
            error="High variance in results across seeds (std=5.2%)",
        ),
    ),
    "consistency_feedback": [
        "Increase sample size from 3 to 10 runs for statistical validity",
        "Add more baseline optimizers and proper statistical testing with p-values",
    ],
}
