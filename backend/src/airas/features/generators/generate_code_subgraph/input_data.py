from airas.types.experimental_design import (
    EvaluationMetric,
    ExperimentalDesign,
    MethodConfig,
    OptunaConfig,
    RunnerConfig,
    SearchSpace,
    TrainingConfig,
)
from airas.types.research_hypothesis import ResearchHypothesis

generate_code_subgraph_input_data = {
    "research_hypothesis": ResearchHypothesis(
        open_problems="Diffusion models suffer from slow sampling speed",
        method="Improve sampling efficiency with adaptive step sizes",
        experimental_setup="Test on CIFAR-10 and ImageNet64 datasets using pre-trained DDPM models",
        primary_metric="FID (Fréchet Inception Distance)",
        experimental_code="PyTorch + diffusers library, CPU-only inference",
        expected_result="5-8× reduction in sampling steps while maintaining generation quality (FID ≤ baseline)",
        expected_conclusion="Adaptive higher-order ODE solver enables training-free acceleration of diffusion models",
    ),
    "experimental_design": ExperimentalDesign(
        experiment_summary="Validate that Adaptive Higher-Order Free (AHOF) sampler accelerates diffusion sampling without retraining. Compare against DDIM and DPM-Solver++ baselines on CIFAR-10 and ImageNet64.",
        runner_config=RunnerConfig(
            runner_label="ubuntu-latest",
            description="CPU-only inference using fp16 precision. Pre-trained models loaded to CPU with aggressive memory management.",
        ),
        evaluation_metrics=[
            EvaluationMetric(
                name="FID",
                description="Fréchet Inception Distance - measures distribution similarity between generated and real images. Lower is better.",
            ),
            EvaluationMetric(
                name="Sampling Time",
                description="Wall-clock time (seconds) to generate 1000 samples. Lower is better.",
            ),
        ],
        models_to_use=["DDPM-CIFAR10-24M", "DDPM-ImageNet64-50M"],
        datasets_to_use=["CIFAR-10", "ImageNet64"],
        proposed_method=MethodConfig(
            method_name="AHOF",
            description="Adaptive Higher-Order Free sampler using 3rd-order Adams-Bashforth predictor with adaptive step-size control",
            training_config=TrainingConfig(
                learning_rate=None,
                batch_size=20,
                epochs=None,
                optimizer=None,
                seed=42,
            ),
            optuna_config=OptunaConfig(
                enabled=True,
                n_trials=15,
                search_spaces=[
                    SearchSpace(
                        param_name="error_tolerance",
                        distribution_type="loguniform",
                        low=1e-4,
                        high=1e-2,
                    ),
                    SearchSpace(
                        param_name="step_size_scale",
                        distribution_type="uniform",
                        low=0.8,
                        high=1.5,
                    ),
                    SearchSpace(
                        param_name="max_order",
                        distribution_type="categorical",
                        choices=[2, 3, 4],
                    ),
                ],
            ),
        ),
        comparative_methods=[
            MethodConfig(
                method_name="DDIM",
                description="Denoising Diffusion Implicit Models with 15 fixed steps",
                training_config=TrainingConfig(batch_size=20, seed=42),
            ),
            MethodConfig(
                method_name="DPM-Solver++",
                description="2nd-order DPM-Solver++ with 10 steps",
                training_config=TrainingConfig(batch_size=20, seed=42),
            ),
        ],
    ),
}
