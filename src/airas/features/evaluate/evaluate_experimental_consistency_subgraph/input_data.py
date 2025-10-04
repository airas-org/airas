from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import (
    Experiment,
    ExperimentalDesign,
    ExperimentalResults,
    ResearchHypothesis,
)

evaluate_experimental_consistency_subgraph_input_data = {
    "new_method": ResearchHypothesis(
        method="Adaptive Curvature Momentum (ACM) Optimizer for improved convergence in deep learning",
        experimental_design=ExperimentalDesign(
            experiment_strategy="Compare ACM against Adam/SGD/AdaBelief on ResNet-18 using CIFAR-10",
            experiments=[
                Experiment(
                    experiment_id="exp-1",
                    description="Baseline comparison: ACM vs Adam/SGD/AdaBelief on CIFAR-10",
                    run_variations=[
                        "baseline_adam",
                        "baseline_sgd",
                        "baseline_adabelief",
                        "proposed_acm",
                    ],
                    results=ExperimentalResults(
                        result="Training completed successfully. Final metrics: ACM accuracy=94.2%, Adam=92.1%, SGD=89.7%, AdaBelief=93.5%. Convergence: ACM at 45 epochs, Adam at 55 epochs.",
                        error=None,
                        image_file_name_list=[
                            "training_loss.pdf",
                            "accuracy_comparison.pdf",
                        ],
                    ),
                ),
                Experiment(
                    experiment_id="exp-2",
                    description="Ablation study: Impact of curvature-aware adjustment",
                    run_variations=["acm_full", "acm_no_curvature", "acm_no_momentum"],
                    results=ExperimentalResults(
                        result="Ablation results: ACM full=94.2%, ACM without curvature=92.8%, ACM without momentum=91.5%. Curvature adjustment provides 1.4% improvement.",
                        error="Training instability observed in acm_no_momentum variant at epoch 35",
                        image_file_name_list=["ablation_comparison.pdf"],
                    ),
                ),
            ],
        ),
    ),
    "github_repository_info": GitHubRepositoryInfo(
        github_owner="auto-res2",
        repository_name="experiment_matsuzawa_251001",
        branch_name="research-20251001-051610-001",
    ),
}
