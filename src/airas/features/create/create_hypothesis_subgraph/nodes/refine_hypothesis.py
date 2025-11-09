from jinja2 import Environment

from airas.features.create.create_hypothesis_subgraph.prompt.refine_hypothesis_prompt import (
    refine_hypothesis_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.research_hypothesis import (
    EvaluatedHypothesis,
    ResearchHypothesis,
)
from airas.types.research_study import ResearchStudy


def refine_hypothesis(
    llm_name: LLM_MODEL,
    llm_client: LLMFacadeClient,
    research_topic: str,
    evaluated_hypothesis_history: list[EvaluatedHypothesis],
    research_study_list: list[ResearchStudy],
) -> ResearchHypothesis:
    env = Environment()

    if not evaluated_hypothesis_history:
        raise ValueError(
            "evaluated_hypothesis_history must contain at least one hypothesis"
        )

    latest = evaluated_hypothesis_history[-1]

    template = env.from_string(refine_hypothesis_prompt)
    data = {
        "research_topic": research_topic,
        "current_hypothesis": latest.hypothesis.to_formatted_json(),
        "novelty_reason": latest.evaluation.novelty_reason,
        "significance_reason": latest.evaluation.significance_reason,
        "evaluated_hypothesis_history": EvaluatedHypothesis.format_list(
            evaluated_hypothesis_history[:-1]
        ),
        "research_study_list": ResearchStudy.format_list(research_study_list),
    }
    messages = template.render(data)
    output, cost = llm_client.structured_outputs(
        message=messages,
        data_model=ResearchHypothesis,
    )
    if output is None:
        raise ValueError("No response from LLM in refine_hypothesis")

    return ResearchHypothesis(**output)
