from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import (
    Experiment,
    ExperimentalDesign,
    ExperimentalResults,
    ExperimentEvaluation,
    ResearchHypothesis,
)

analytic_subgraph_input_data = {
    "new_method": ResearchHypothesis(
        method="Q-Denoising Diffusion Probe (QD²P) - a method that uses a lightweight, linear Q-probe to guide diffusion denoising process.",
        experimental_design=ExperimentalDesign(
            experiment_strategy="Experimental plan with three concrete experiments using PyTorch, NumPy, and visualization tools.",
            experiments=[
                Experiment(
                    experiment_id="exp-1",
                    description="Quality comparison: QD²P vs standard diffusion on image generation",
                    run_variations=["baseline_diffusion", "proposed_qd2p"],
                    results=ExperimentalResults(
                        result="QD²P achieves FID score of 12.3 vs baseline 15.7, demonstrating superior image quality with 21.6% improvement.",
                        image_file_name_list=[
                            "quality_comparison.pdf",
                            "sample_images.pdf",
                        ],
                    ),
                    evaluation=ExperimentEvaluation(
                        consistency_score=9,
                        consistency_feedback="Excellent experimental design with clear results supporting claims.",
                        is_selected_for_paper=True,
                    ),
                ),
                Experiment(
                    experiment_id="exp-2",
                    description="Speed analysis: Inference time comparison",
                    run_variations=["baseline", "qd2p_distilled"],
                    results=ExperimentalResults(
                        result="QD²P with distillation achieves 6.30x speedup (0.15s vs 0.95s per image) with 100% quality retention.",
                        image_file_name_list=["speed_comparison.pdf"],
                    ),
                    evaluation=ExperimentEvaluation(
                        consistency_score=8,
                        consistency_feedback="Strong evidence of speedup with maintained quality.",
                        is_selected_for_paper=True,
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
