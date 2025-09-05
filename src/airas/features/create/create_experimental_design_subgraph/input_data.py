from airas.types.research_hypothesis import (
    ExperimentalDesign,
    ExperimentalResults,
    ResearchHypothesis,
)

create_experimental_design_subgraph_input_data = {
    "new_method": ResearchHypothesis(
        method="Adaptive Curvature Momentum (ACM) Optimizer for improved convergence in deep learning",
        experimental_design=ExperimentalDesign(
            experiment_strategy="Compare ACM against Adam/SGD on ResNet-18 using CIFAR-10",
            experiment_details="Train for 100 epochs, 3 seeds, track loss/accuracy curves",
            experiment_code="PyTorch implementation with custom optimizer class",
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
