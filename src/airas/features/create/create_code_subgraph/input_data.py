from airas.types.github import GitHubRepositoryInfo
from airas.types.hugging_face import HuggingFace, HuggingFaceResource
from airas.types.research_hypothesis import (
    ExperimentalDesign,
    ExternalResources,
    ResearchHypothesis,
)

dummy_external_resources = ExternalResources(
    hugging_face=HuggingFace(
        models=[
            HuggingFaceResource(
                id="microsoft/DialoGPT-medium",
                author="microsoft",
                downloads=1000000,
                likes=500,
                pipeline_tag="conversational",
            )
        ],
        datasets=[
            HuggingFaceResource(
                id="squad",
                author="rajpurkar",
                downloads=500000,
                likes=200,
                pipeline_tag="question-answering",
            )
        ],
    )
)

dummy_experimental_design = ExperimentalDesign(
    experiment_strategy="Test strategy for validation",
    experiment_details="Simple test details for validation",
    expected_models=["test-model"],
    expected_datasets=["test-dataset"],
    external_resources=dummy_external_resources,
)

dummy_research_hypothesis = ResearchHypothesis(
    method="Simple test method for validation",
    experimental_design=dummy_experimental_design,
)

dummy_github_repo = GitHubRepositoryInfo(
    github_owner="auto-res2",
    repository_name="experiment_matsuzawa_20250911",
    branch_name="research-20250911-160618-003",
)

create_code_subgraph_input_data = {
    "github_repository_info": dummy_github_repo,
    "new_method": dummy_research_hypothesis,
    "experiment_iteration": 1,
}
