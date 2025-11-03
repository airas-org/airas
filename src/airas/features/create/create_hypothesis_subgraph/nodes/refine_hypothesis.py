from jinja2 import Environment

from airas.features.create.create_hypothesis_subgraph.prompt.refine_hypothesis_prompt import (
    refine_hypothesis_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_idea import (
    GenerateIdea,
    ResearchIdea,
)
from airas.types.research_study import ResearchStudy
from airas.utils.save_prompt import save_io_on_github


def refine_hypothesis(
    llm_name: LLM_MODEL,
    research_topic: str,
    evaluated_idea_info: ResearchIdea,
    research_study_list: list[ResearchStudy],
    idea_info_history: list[ResearchIdea],
    refine_iterations: int,
    github_repository_info: GitHubRepositoryInfo,
    client: LLMFacadeClient | None = None,
) -> ResearchIdea:
    client = client or LLMFacadeClient(llm_name=llm_name)
    env = Environment()

    template = env.from_string(refine_hypothesis_prompt)
    data = {
        "research_topic": research_topic,
        "evaluated_idea_info": evaluated_idea_info.idea.to_formatted_json(),
        "novelty_reason": evaluated_idea_info.evaluation.novelty_reason,
        "significance_reason": evaluated_idea_info.evaluation.significance_reason,
        "idea_info_history": ResearchIdea.format_list(idea_info_history),
        "research_study_list": ResearchStudy.format_list(research_study_list),
    }
    messages = template.render(data)
    output, cost = client.structured_outputs(
        message=messages,
        data_model=GenerateIdea,
    )
    if output is None:
        raise ValueError("No response from LLM in refine_hypothesis")
    save_io_on_github(
        github_repository_info=github_repository_info,
        input=messages,
        output=str(output),
        subgraph_name="create_hypothesis_subgraph",
        node_name=f"refine_hypothesis_{refine_iterations}",
        llm_name=llm_name,
    )
    new_idea_info = ResearchIdea(idea=GenerateIdea(**output))
    return new_idea_info
