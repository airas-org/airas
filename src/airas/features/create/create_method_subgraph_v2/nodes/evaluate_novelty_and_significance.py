from jinja2 import Environment

from airas.features.create.create_method_subgraph.nodes.idea_generator import (
    parse_research_study_list,
)
from airas.features.create.create_method_subgraph_v2.prompt.evaluate_novelty_and_significance_prompt import (
    evaluate_novelty_and_significance_prompt,
)
from airas.features.create.create_method_subgraph_v2.types import (
    GenerateIdea,
    IdeaEvaluationResults,
    ResearchIdea,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.research_study import ResearchStudy


def evaluate_novelty_and_significance(
    research_topic: str,
    research_study_list: list[ResearchStudy],
    new_idea_info: ResearchIdea,
    llm_name: LLM_MODEL,
    client: LLMFacadeClient | None = None,
) -> IdeaEvaluationResults:
    client = client or LLMFacadeClient(llm_name=llm_name)
    env = Environment()

    template = env.from_string(evaluate_novelty_and_significance_prompt)
    data = {
        "research_topic": research_topic,
        "research_study_list": parse_research_study_list(research_study_list),
        "new_idea_info": parse_new_idea_info(new_idea_info["idea"]),
    }
    messages = template.render(data)
    output, cost = client.structured_outputs(
        message=messages,
        data_model=IdeaEvaluationResults,
    )
    if output is None:
        raise ValueError("No response from LLM in idea_generator.")
    return output


def parse_new_idea_info(new_idea_info: GenerateIdea) -> str:
    return f"""\
Open Problems: {new_idea_info.open_problems}
Methods: {new_idea_info.methods}
Experimental Setup: {new_idea_info.experimental_setup}
Result: {new_idea_info.result}
Conclusion: {new_idea_info.conclusion}"""
