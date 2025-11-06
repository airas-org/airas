import json
from logging import getLogger

from dependency_injector import providers
from dependency_injector.wiring import Provide, inject
from jinja2 import Environment
from pydantic import BaseModel

from airas.features.analysis.analytic_subgraph.prompt.evaluate_method_prompt import (
    evaluate_method_prompt,
)
from airas.services.api_client.api_clients_container import SyncContainer
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
    method_feedback: str


@inject
def evaluate_method(
    llm_name: LLM_MODEL,
    new_method: ResearchHypothesis,
    hypothesis_history: list[ResearchHypothesis],
    github_repository_info: GitHubRepositoryInfo,
    llm_facade_provider: providers.Factory[LLMFacadeClient] = Provide[
        SyncContainer.llm_facade_provider
    ],
) -> ResearchHypothesis:
    client = llm_facade_provider(llm_name=llm_name)

    env = Environment()
    template = env.from_string(evaluate_method_prompt)

    data = {
        "new_method": new_method.model_dump(),
        "hypothesis_history": [h.model_dump() for h in hypothesis_history],
    }
    messages = template.render(data)
    output, cost = client.structured_outputs(message=messages, data_model=LLMOutput)
    if output is None:
        raise ValueError("No response from LLM in evaluate_methods.")

    save_io_on_github(
        github_repository_info=github_repository_info,
        input=messages,
        output=json.dumps(output, ensure_ascii=False, indent=4),
        subgraph_name="analytic_subgraph",
        node_name="evaluate_methods",
        llm_name=llm_name,
    )

    if new_method.experimental_analysis is None:
        new_method.experimental_analysis = ExperimentalAnalysis()

    if new_method.experimental_analysis.evaluation is None:
        new_method.experimental_analysis.evaluation = ExperimentEvaluation()

    new_method.experimental_analysis.evaluation.method_feedback = output[
        "method_feedback"
    ]

    return new_method
