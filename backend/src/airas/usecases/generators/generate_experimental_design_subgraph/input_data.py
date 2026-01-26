from airas.core.types.experimental_design import RunnerConfig
from airas.core.types.research_hypothesis import ResearchHypothesis

default_runner_config = RunnerConfig(
    runner_label="ubuntu-latest",
    description="Standard GitHub Actions runner with 2-core CPU, 7 GB RAM, 14 GB SSD. Suitable for lightweight ML experiments and CPU-based training.",
)

generate_experimental_design_subgraph_input_data = {
    "research_hypothesis": ResearchHypothesis(
        open_problems="Diffusion models suffer from slow sampling speed",
        method="Improve existing method with adaptive step sizes",
        experimental_setup="Test on CIFAR-10 and ImageNet datasets",
        experimental_code="Using PyTorch and diffusers library",
        expected_result="Achieve even better convergence",
        expected_conclusion="Further acceleration",
        primary_metric="FID",
    ),
}
