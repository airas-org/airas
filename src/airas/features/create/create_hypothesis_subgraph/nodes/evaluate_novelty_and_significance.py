from dependency_injector import providers
from dependency_injector.wiring import Provide, inject
from jinja2 import Environment

from airas.features.create.create_hypothesis_subgraph.prompt.evaluate_novelty_and_significance_prompt import (
    evaluate_novelty_and_significance_prompt,
)
from airas.services.api_client.api_clients_container import SyncContainer
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_idea import (
    GenerateIdea,
    IdeaEvaluationResults,
)
from airas.types.research_study import ResearchStudy
from airas.utils.save_prompt import save_io_on_github


@inject
def evaluate_novelty_and_significance(
    research_topic: str,
    research_study_list: list[ResearchStudy],
    new_idea: GenerateIdea,
    llm_name: LLM_MODEL,
    github_repository_info: GitHubRepositoryInfo,
    llm_facade_provider: providers.Factory[LLMFacadeClient] = Provide[
        SyncContainer.llm_facade_provider
    ],
) -> IdeaEvaluationResults:
    client = llm_facade_provider(llm_name=llm_name)
    env = Environment()

    template = env.from_string(evaluate_novelty_and_significance_prompt)
    data = {
        "research_topic": research_topic,
        "research_study_list": ResearchStudy.format_list(research_study_list),
        "new_idea_info": new_idea.to_formatted_json(),
    }
    messages = template.render(data)
    output, cost = client.structured_outputs(
        message=messages,
        data_model=IdeaEvaluationResults,
    )
    save_io_on_github(
        github_repository_info=github_repository_info,
        input=messages,
        output=str(output),
        subgraph_name="create_hypothesis_subgraph",
        node_name="evaluate_novelty_and_significance",
        llm_name=llm_name,
    )
    if output is None:
        raise ValueError("No response from LLM in idea_generator.")
    return IdeaEvaluationResults(**output)
