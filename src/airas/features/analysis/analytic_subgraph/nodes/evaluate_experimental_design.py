import json
from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.features.analysis.analytic_subgraph.prompt.evaluate_experimental_design_prompt import (
    evaluate_experimental_design_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import (
    ExperimentalAnalysis,
    ExperimentEvaluation,
    ResearchHypothesis,
)
from airas.utils.save_prompt import save_io_on_github

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    design_feedback: str


def evaluate_experimental_design(
    llm_name: LLM_MODEL,
    new_method: ResearchHypothesis,
    github_repository_info: GitHubRepositoryInfo,
    client: LLMFacadeClient | None = None,
) -> ResearchHypothesis:
    if client is None:
        client = LLMFacadeClient(llm_name=llm_name)

    env = Environment()
    template = env.from_string(evaluate_experimental_design_prompt)

    data = {"new_method": new_method.model_dump()}
    messages = template.render(data)
    output, cost = client.structured_outputs(message=messages, data_model=LLMOutput)
    if output is None:
        raise ValueError("No response from LLM in evaluate_experimental_design.")

    save_io_on_github(
        github_repository_info=github_repository_info,
        input=messages,
        output=json.dumps(output, ensure_ascii=False, indent=4),
        subgraph_name="analytic_subgraph",
        node_name="evaluate_experimental_design",
        llm_name=llm_name,
    )

    if new_method.experimental_analysis is None:
        new_method.experimental_analysis = ExperimentalAnalysis()

    if new_method.experimental_analysis.evaluation is None:
        new_method.experimental_analysis.evaluation = ExperimentEvaluation()

    new_method.experimental_analysis.evaluation.design_feedback = output[
        "design_feedback"
    ]

    return new_method
