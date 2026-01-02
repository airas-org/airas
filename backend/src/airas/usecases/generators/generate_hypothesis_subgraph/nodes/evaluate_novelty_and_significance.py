from jinja2 import Environment

from airas.core.types.research_hypothesis import (
    EvaluatedHypothesis,
    HypothesisEvaluation,
    ResearchHypothesis,
)
from airas.core.types.research_study import ResearchStudy
from airas.infra.langchain_client import LangChainClient
from airas.infra.llm_specs import LLM_MODELS
from airas.usecases.generators.generate_hypothesis_subgraph.prompts.evaluate_novelty_and_significance_prompt import (
    evaluate_novelty_and_significance_prompt,
)


async def evaluate_novelty_and_significance(
    research_topic: str,
    research_study_list: list[ResearchStudy],
    research_hypothesis: ResearchHypothesis,
    llm_name: LLM_MODELS,
    llm_client: LangChainClient,
) -> EvaluatedHypothesis:
    env = Environment()

    template = env.from_string(evaluate_novelty_and_significance_prompt)
    data = {
        "research_topic": research_topic,
        "research_study_list": [
            ResearchStudy.to_formatted_json(research_study)
            for research_study in research_study_list
        ],
        "new_hypothesis": research_hypothesis.to_formatted_json(),
    }
    messages = template.render(data)
    output = await llm_client.structured_outputs(
        message=messages,
        data_model=HypothesisEvaluation,
        llm_name=llm_name,
    )

    if output is None:
        raise ValueError("No response from LLM in evaluate_novelty_and_significance.")
    return EvaluatedHypothesis(hypothesis=research_hypothesis, evaluation=output)
