from airas.core.types.github import GitHubRepositoryInfo
from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.core.types.research_iteration import (
    ExperimentalDesign,
    ExperimentRun,
    ResearchIteration,
)
from airas.core.types.research_session import ResearchSession

retrieve_hugging_face_subgraph_input_data = {
    "research_session": ResearchSession(
        hypothesis=ResearchHypothesis(
            open_problems="Diffusion models suffer from slow sampling speed",
            method="Improve existing method with adaptive step sizes",
            experimental_setup="Test on CIFAR-10 and ImageNet datasets",
            experimental_code="Using PyTorch and diffusers library",
            expected_result="Achieve even better convergence",
            expected_conclusion="Further acceleration",
        ),
        iterations=[
            ResearchIteration(
                method="Propose a novel training-free acceleration method using higher-order approximation",
                experimental_design=ExperimentalDesign(
                    experiment_summary='Purpose: Validate that the proposed Adaptive Higher-Order Free (AHOF) sampler accelerates diffusion model sampling without retraining.\nComponents:\n1. Pre-trained diffusion backbones\n   • DDPM-CIFAR10-24M (32×32)\n   • DDPM-ImageNet64-50M (64×64)\n2. Samplers\n   • Proposed AHOF (ours)\n   • Baselines: DDIM and DPM-Solver++ (2M)\n3. Datasets\n   • CIFAR-10 test split (10 k images, we down-sample to 2 k to fit the 500 MB CPU RAM)\n   • ImageNet64 validation split (50 k images, we down-sample to 5 k)\nWorkflow:\nA. Load each pre-trained model in fp16-cpu mode with torch.load(map_location="cpu"), keeping only the UNet weights to stay within memory.\nB. For each sampler (AHOF, DDIM15, DPM-Solver++10):\n   1. Generate 50 batches × 20 images (1 000 samples) for CIFAR-10 and 100 batches × 20 images (2 000 samples) for ImageNet64.\n   2. Measure wall-clock sampling time and number of function evaluations (NFE).\nC. Compute FID and Inception Score on the generated sets using pre-extracted features (cached numpy arrays) to avoid GPU need.\nD. Grid-search three AHOF hyper-parameters using 5-fold cross-validation on 200 validation samples, select the best setting, and re-run Step B.\nE. Report metrics, produce convergence plots (FID vs NFE) and speed-up ratios.\nThe entire pipeline is written in PyTorch + diffusers, CPU-only, with aggressive memory-freeing (del & torch.cuda.empty_cache()) and torch.set_grad_enabled(False) for inference.',
                    evaluation_metrics=[
                        "FID",
                        "Inception Score",
                        "Sampling Time (s)",
                        "Number of Function Evaluations",
                    ],
                    proposed_method="Adaptive Higher-Order Free (AHOF) Sampler\nObjective: Reduce sampling steps of diffusion models by combining (i) third-order predictor–corrector (PC) ODE solver, (ii) embedded second-order error estimator, and (iii) adaptive step-size controller.\nTheory: Starting from the probability flow ODE dx/dt = f(x,t), AHOF uses a 3-step Adams–Bashforth predictor followed by a single trapezoidal corrector. The local truncation error is estimated via the difference between the third-order solution and an internally computed second-order solution. If the error e_t exceeds a tolerance ε, the step size h is scaled by 0.9·(ε/e_t)^(1/3); otherwise the step is accepted and h is increased up to h_max = α·h_prev (α ∈ [1,1.5]). This adaptive strategy prevents over-stepping early in the trajectory and allows large jumps near t≈0 where the ODE stiffens.\nAlgorithmic Steps:\n1. Initialise x_T ~ N(0,I), set current time t=T, choose initial h=T/N (N=50 by default).\n2. While t>0:\n   a. Predictor: x_p = x_k + h·Σ_{i=1}^{3} β_i f_{k−i+1} (β from 3-step AB).\n   b. Corrector: f_p = f(x_p,t−h); x_c = x_k + h/2·(f_k + f_p).\n   c. Error: e = ||x_c − x_p||_2 / ||x_c||_2.\n   d. If e ≤ ε accept x_{k+1}=x_c, store f_k, decrease t ← t−h; else reject and halve h.\n   e. Update h for next step using scaling rule, clipped to [h_min,h_max].\n3. Return x_0 as the generated sample.\nThe method is training-free, requires one extra model evaluation per step (for f_p), but achieves 5–8× fewer accepted steps than DDIM while preserving quality.\nImplementation: Extend diffusers.DPMSolverStep with adaptive controller, add caching of past gradients to support multi-step formula, and expose three tunable hyper-parameters: ε (error_tolerance), α (step_size_scale), and max_order (2–4).",
                    comparative_methods=[
                        "DDIM (15 fixed steps)",
                        "DPM-Solver++ (2nd-order, 10 steps)",
                    ],
                    models_to_use=["DDPM-CIFAR10-24M", "DDPM-ImageNet64-50M"],
                    datasets_to_use=["CIFAR-10", "ImageNet64"],
                    hyperparameters_to_search={
                        "error_tolerance": "1e-4-1e-2",
                        "step_size_scale": "0.8-1.5",
                        "max_order": "2,3,4",
                    },
                    external_resources=None,
                    experiment_code=None,
                ),
                experiment_runs=[
                    ExperimentRun(
                        run_id="proposed-DDPM-CIFAR10-24M-CIFAR-10",
                        method_name="proposed",
                        model_name="DDPM-CIFAR10-24M",
                        dataset_name="CIFAR-10",
                        run_config=None,
                        github_repository_info=None,
                        results=None,
                    ),
                    ExperimentRun(
                        run_id="proposed-DDPM-CIFAR10-24M-ImageNet64",
                        method_name="proposed",
                        model_name="DDPM-CIFAR10-24M",
                        dataset_name="ImageNet64",
                        run_config=None,
                        github_repository_info=None,
                        results=None,
                    ),
                ],
            ),
        ],
    ),
    "github_repository_info": GitHubRepositoryInfo(
        github_owner="auto-res2",
        repository_name="airas-20251009-055033-matsuzawa",
        branch_name="main",
    ),
}
