from jinja2 import Environment

from airas.features.create.create_method_subgraph.nodes.idea_generator import (
    parse_research_study_list,
)
from airas.features.create.create_method_subgraph_v2.nodes.evaluate_novelty_and_significance import (
    parse_new_idea_info,
)
from airas.features.create.create_method_subgraph_v2.prompt.refine_ide_and_research_summary_prompt import (
    refine_ide_and_research_summary_prompt,
)
from airas.features.create.create_method_subgraph_v2.types import (
    GenerateIdea,
    ResearchIdea,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.research_study import ResearchStudy


def refine_idea_and_research_summary(
    llm_name: LLM_MODEL,
    research_topic: str,
    evaluated_idea_info: ResearchIdea,
    research_study_list: list[ResearchStudy],
    idea_info_history: list[ResearchIdea],
    client: LLMFacadeClient | None = None,
) -> tuple[dict[str, str], list[dict[str, str]]]:
    client = client or LLMFacadeClient(llm_name=llm_name)
    env = Environment()

    template = env.from_string(refine_ide_and_research_summary_prompt)
    data = {
        "research_topic": research_topic,
        "evaluated_idea_info": parse_new_idea_info(evaluated_idea_info["idea"]),
        "novelty_reason": evaluated_idea_info["evaluate"].novelty_reason,
        "significance_reason": evaluated_idea_info["evaluate"].significance_reason,
        "idea_info_history": parse_idea_info_history(idea_info_history),
        "research_study_list": parse_research_study_list(research_study_list),
    }
    messages = template.render(data)
    output, cost = client.structured_outputs(
        message=messages,
        data_model=GenerateIdea,
    )
    if output is None:
        raise ValueError("No response from LLM in idea_generator.")

    idea_info_history.append(evaluated_idea_info)
    return output, idea_info_history


def parse_idea_info_history(idea_info_history: list[ResearchIdea]) -> str:
    idea_info_history_str = ""
    for idea_info in idea_info_history:
        idea_info_str = parse_new_idea_info(idea_info["idea"])
        idea_eval_str = f"""\
Novelty: {idea_info["evaluate"].novelty_reason}
Significance: {idea_info["evaluate"].significance_reason}
"""
        idea_info_history_str += f"Idea Info:\n{idea_info_str}\n{idea_eval_str}\n"
    return idea_info_history_str
