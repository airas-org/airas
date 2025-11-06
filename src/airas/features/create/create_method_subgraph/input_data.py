from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.research_iteration import ResearchIteration
from airas.types.research_session import ResearchSession
from airas.types.research_study import ResearchStudy

# Test data for initial creation (empty iterations)
create_method_subgraph_input_data_initial = {
    "research_session": ResearchSession(
        hypothesis=ResearchHypothesis(
            open_problems="Diffusion models suffer from slow sampling speed",
            method="Propose a novel training-free acceleration method using higher-order approximation",
            experimental_setup="Test on CIFAR-10 and ImageNet datasets",
            experimental_code="Using PyTorch and diffusers library",
            expected_result="Achieve O(1/T^2) convergence rate",
            expected_conclusion="Faster sampling without quality degradation",
        ),
        iterations=[],  # Empty for initial creation
    ),
    "research_study_list": [
        ResearchStudy(title="Characteristic Guidance for Diffusion Models"),
        ResearchStudy(title="Align Your Steps: Optimizing Sampling Schedules"),
    ],
    "github_repository_info": GitHubRepositoryInfo(
        github_owner="auto-res2",
        repository_name="airas-20251009-055033-matsuzawa",
        branch_name="main",
    ),
}

# Test data for improvement (with existing iterations)
create_method_subgraph_input_data_improve = {
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
    "research_study_list": [
        ResearchStudy(title="Characteristic Guidance for Diffusion Models"),
        ResearchStudy(title="Align Your Steps: Optimizing Sampling Schedules"),
    ],
    "github_repository_info": GitHubRepositoryInfo(
        github_owner="auto-res2",
        repository_name="airas-20251009-055033-matsuzawa",
        branch_name="main",
    ),
}

# Default to initial creation
create_method_subgraph_input_data = create_method_subgraph_input_data_improve
