from pydantic import BaseModel

from airas.types.latex import LATEX_TEMPLATE_NAME
from airas.types.paper import PaperContent
from src.airas.types.github import GitHubConfig


class GenerateLatexSubgraphRequestBody(BaseModel):
    references_bib: str
    paper_content: PaperContent
    latex_template_name: LATEX_TEMPLATE_NAME = "iclr2024"


class GenerateLatexSubgraphResponseBody(BaseModel):
    latex_text: str
    execution_time: dict[str, list[float]]


class PushLatexSubgraphRequestBody(BaseModel):
    github_config: GitHubConfig
    latex_text: str
    latex_template_name: LATEX_TEMPLATE_NAME = "iclr2024"


class PushLatexSubgraphResponseBody(BaseModel):
    is_upload_successful: bool
    is_images_prepared: bool
    execution_time: dict[str, list[float]]
