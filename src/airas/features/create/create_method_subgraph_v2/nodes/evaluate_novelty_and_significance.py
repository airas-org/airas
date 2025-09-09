from jinja2 import Environment

from airas.features.create.create_method_subgraph.nodes.idea_generator import (
    parse_research_study_list,
)
from airas.features.create.create_method_subgraph_v2.prompt.evaluate_novelty_and_significance_prompt import (
    evaluate_novelty_and_significance_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.research_idea import (
    GenerateIdea,
    IdeaEvaluationResults,
)
from airas.types.research_study import ResearchStudy


def evaluate_novelty_and_significance(
    research_topic: str,
    research_study_list: list[ResearchStudy],
    new_idea: GenerateIdea,
    llm_name: LLM_MODEL,
    client: LLMFacadeClient | None = None,
) -> IdeaEvaluationResults:
    client = client or LLMFacadeClient(llm_name=llm_name)
    env = Environment()

    template = env.from_string(evaluate_novelty_and_significance_prompt)
    data = {
        "research_topic": research_topic,
        "research_study_list": parse_research_study_list(research_study_list),
        "new_idea_info": parse_new_idea_info(new_idea),
    }
    messages = template.render(data)
    output, cost = client.structured_outputs(
        message=messages,
        data_model=IdeaEvaluationResults,
    )
    if output is None:
        raise ValueError("No response from LLM in idea_generator.")
    return IdeaEvaluationResults(**output)


def parse_new_idea_info(new_idea: GenerateIdea) -> str:
    return f"""\
Open Problems: {new_idea.open_problems}
Methods: {new_idea.methods}
Experimental Setup: {new_idea.experimental_setup}
Expected Result: {new_idea.expected_result}
Expected Conclusion: {new_idea.expected_conclusion}"""
