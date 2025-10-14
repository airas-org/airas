from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import (
    ExperimentalDesign,
    ExperimentRun,
    ResearchHypothesis,
)

dummy_experimental_design = ExperimentalDesign(
    experiment_summary="Comparative analysis of efficient model architectures across vision and language tasks",
    evaluation_metrics=["accuracy", "f1_score", "inference_time", "model_size"],
    proposed_method="Evaluate MobileNetV2 and DistilBERT variants for efficient deployment",
    comparative_methods=[
        "MobileNetV2-0.5 (3.5M parameters)",
        "DistilBERT-base (66M parameters)",
    ],
    models_to_use=["MobileNetV2-0.5-3.5M", "DistilBERT-base-66M"],
    datasets_to_use=["CIFAR-10", "alpaca-cleaned"],
)

dummy_experiment_runs = [
    ExperimentRun(
        run_id="comparative-2-MobileNetV2-0.5-3.5M-CIFAR-10",
        method_name="comparative-2",
        model_name="MobileNetV2-0.5-3.5M",
        dataset_name="CIFAR-10",
    ),
    ExperimentRun(
        run_id="comparative-2-MobileNetV2-0.5-3.5M-alpaca-cleaned",
        method_name="comparative-2",
        model_name="MobileNetV2-0.5-3.5M",
        dataset_name="alpaca-cleaned",
    ),
    ExperimentRun(
        run_id="comparative-2-DistilBERT-base-66M-CIFAR-10",
        method_name="comparative-2",
        model_name="DistilBERT-base-66M",
        dataset_name="CIFAR-10",
    ),
    ExperimentRun(
        run_id="comparative-2-DistilBERT-base-66M-alpaca-cleaned",
        method_name="comparative-2",
        model_name="DistilBERT-base-66M",
        dataset_name="alpaca-cleaned",
    ),
]

dummy_research_hypothesis = ResearchHypothesis(
    method="We compare lightweight model architectures (MobileNetV2-0.5 and DistilBERT-base) across vision and language tasks to evaluate their efficiency and performance trade-offs.",
    experimental_design=dummy_experimental_design,
    experiment_runs=dummy_experiment_runs,
)

dummy_github_repo = GitHubRepositoryInfo(
    github_owner="auto-res2",
    repository_name="20251014-matsuzawa",
    branch_name="develop",
)

create_code_subgraph_input_data = {
    "github_repository_info": dummy_github_repo,
    "new_method": dummy_research_hypothesis,
}
