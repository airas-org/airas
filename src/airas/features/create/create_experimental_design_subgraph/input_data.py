from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.research_iteration import ResearchIteration
from airas.types.research_session import ResearchSession

create_experimental_design_subgraph_input_data = {
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
                method_id=1,
                method="Propose a novel training-free acceleration method using higher-order approximation",
            )
        ],
    ),
    "github_repository_info": GitHubRepositoryInfo(
        github_owner="auto-res2",
        repository_name="airas-20251009-055033-matsuzawa",
        branch_name="main",
    ),
}
