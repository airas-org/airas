from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import (
    ExperimentalDesign,
    ExperimentRun,
    ResearchHypothesis,
)

dummy_experimental_design = ExperimentalDesign(
    experiment_summary="Comparative analysis of DistilBERT performance across vision and language tasks",
    evaluation_metrics=["accuracy", "f1_score", "inference_time"],
    proposed_method="Fine-tuned DistilBERT with task-specific adapters",
    comparative_methods=[
        "Standard DistilBERT fine-tuning",
    ],
    models_to_use=["DistilBERT-base-66M"],
    datasets_to_use=["CIFAR-10", "alpaca-cleaned"],
)

dummy_experiment_runs = [
    # Proposed method
    ExperimentRun(
        run_id="proposed-DistilBERT-base-66M-CIFAR-10",
        method_name="proposed",
        model_name="DistilBERT-base-66M",
        dataset_name="CIFAR-10",
    ),
    ExperimentRun(
        run_id="proposed-DistilBERT-base-66M-alpaca-cleaned",
        method_name="proposed",
        model_name="DistilBERT-base-66M",
        dataset_name="alpaca-cleaned",
    ),
    # Comparative method
    ExperimentRun(
        run_id="comparative-1-DistilBERT-base-66M-CIFAR-10",
        method_name="comparative-1",
        model_name="DistilBERT-base-66M",
        dataset_name="CIFAR-10",
    ),
    ExperimentRun(
        run_id="comparative-1-DistilBERT-base-66M-alpaca-cleaned",
        method_name="comparative-1",
        model_name="DistilBERT-base-66M",
        dataset_name="alpaca-cleaned",
    ),
]

dummy_research_hypothesis = ResearchHypothesis(
    method="We compare DistilBERT with task-specific adapters (proposed) against standard fine-tuning (comparative) across vision and language tasks to evaluate performance improvements.",
    experimental_design=dummy_experimental_design,
    experiment_runs=dummy_experiment_runs,
)

dummy_github_repo = GitHubRepositoryInfo(
    github_owner="auto-res2",
    repository_name="20251016_matsuzawa_2",
    branch_name="research",
)

create_code_subgraph_input_data = {
    "github_repository_info": dummy_github_repo,
    "new_method": dummy_research_hypothesis,
}
