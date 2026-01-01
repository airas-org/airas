from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.services.api_client.langchain_client import LangChainClient
from airas.services.api_client.llm_specs import LLM_MODELS
from airas.types.github import GitHubRepositoryInfo
from airas.types.paper import PaperContent, PaperReviewScores

logger = getLogger(__name__)


class PaperReviewOutput(BaseModel):
    novelty_score: int
    significance_score: int
    reproducibility_score: int
    experimental_quality_score: int


async def review_paper(
    llm_name: LLM_MODELS,
    prompt_template: str,
    paper_content: PaperContent,
    github_repository_info: GitHubRepositoryInfo | None = None,
    client: LangChainClient | None = None,
) -> dict[str, PaperReviewScores]:
    env = Environment()
    template = env.from_string(prompt_template)

    # Dynamically extract all fields from PaperContent and make them available for template
    paper_data = paper_content.model_dump()
    data: dict[str, object] = {"paper_content": paper_data}
    if github_repository_info is not None:
        data["github_repository_info"] = github_repository_info.model_dump()

    messages = template.render(data)
    langchain_client = client or LangChainClient()
    output: PaperReviewOutput | None = await langchain_client.structured_outputs(
        llm_name=llm_name, message=messages, data_model=PaperReviewOutput
    )

    if output is None:
        raise ValueError("No response from LLM in paper_review_node.")

    paper_review_scores = PaperReviewScores(
        novelty_score=output.novelty_score,
        significance_score=output.significance_score,
        reproducibility_score=output.reproducibility_score,
        experimental_quality_score=output.experimental_quality_score,
    )

    return {"paper_review_scores": paper_review_scores}
