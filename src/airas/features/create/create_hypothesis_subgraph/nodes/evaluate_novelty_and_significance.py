from jinja2 import Environment

from airas.features.create.create_hypothesis_subgraph.prompt.evaluate_novelty_and_significance_prompt import (
    evaluate_novelty_and_significance_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.research_hypothesis import (
    EvaluatedHypothesis,
    HypothesisEvaluation,
    ResearchHypothesis,
)
from airas.types.research_study import ResearchStudy


async def evaluate_novelty_and_significance(
    research_topic: str,
    research_study_list: list[ResearchStudy],
    research_hypothesis: ResearchHypothesis,
    llm_name: LLM_MODEL,
    llm_client: LLMFacadeClient,
) -> EvaluatedHypothesis:
    env = Environment()

    template = env.from_string(evaluate_novelty_and_significance_prompt)
    data = {
        "research_topic": research_topic,
        "research_study_list": ResearchStudy.format_list(research_study_list),
        "new_hypothesis": research_hypothesis.to_formatted_json(),
    }
    messages = template.render(data)
    output, cost = await llm_client.structured_outputs(
        message=messages,
        data_model=HypothesisEvaluation,
        llm_name=llm_name,
    )

    if output is None:
        raise ValueError("No response from LLM in idea_generator.")
    return EvaluatedHypothesis(
        hypothesis=research_hypothesis, evaluation=HypothesisEvaluation(**output)
    )
