from jinja2 import Environment

from airas.features.generators.generate_hypothesis_subgraph.prompts.refine_hypothesis_prompt import (
    refine_hypothesis_prompt,
)
from airas.features.retrieve.retrieve_paper_subgraph.nodes.extract_reference_titles import (
    LangChainClient,
)
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.types.research_hypothesis import (
    EvaluatedHypothesis,
    ResearchHypothesis,
)
from airas.types.research_study import ResearchStudy


async def refine_hypothesis(
    llm_name: LLM_MODEL,
    llm_client: LangChainClient,
    research_objective: str,
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
        "research_objective": research_objective,
        "current_hypothesis": latest.hypothesis.to_formatted_json(),
        "novelty_reason": latest.evaluation.novelty_reason,
        "significance_reason": latest.evaluation.significance_reason,
        "evaluated_hypothesis_history": EvaluatedHypothesis.format_list(
            evaluated_hypothesis_history[:-1]
        ),
        "research_study_list": [
            ResearchStudy.to_formatted_json(research_study)
            for research_study in research_study_list
        ],
    }
    messages = template.render(data)
    output, cost = await llm_client.structured_outputs(
        message=messages,
        data_model=ResearchHypothesis,
        llm_name=llm_name,
    )
    if output is None:
        raise ValueError("No response from LLM in refine_hypothesis")

    return output
