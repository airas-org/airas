from pydantic import BaseModel

from airas.types.github import GitHubConfig
from airas.types.latex import LATEX_TEMPLATE_NAME
from airas.types.paper import PaperContent


# TODO: Latex関連の各APIのrequest bodyにlatex_template_nameがあるのを取り除き、GenerateLatexSubgraphRequestBodyだけがもつ様に変更する
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


class CompileLatexSubgraphRequestBody(BaseModel):
    github_config: GitHubConfig
    latex_template_name: LATEX_TEMPLATE_NAME = "iclr2024"


class CompileLatexSubgraphResponseBody(BaseModel):
    is_compiled: bool
    paper_url: str | None
    execution_time: dict[str, list[float]]
