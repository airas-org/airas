from pydantic import BaseModel

from airas.core.types.github import GitHubConfig
from airas.core.types.latex import LATEX_TEMPLATE_NAME
from airas.core.types.paper import PaperContent
from airas.usecases.publication.compile_latex_subgraph.compile_latex_subgraph import (
    CompileLatexLLMMapping,
)
from airas.usecases.publication.generate_latex_subgraph.generate_latex_subgraph import (
    GenerateLatexLLMMapping,
)


# TODO: Latex関連の各APIのrequest bodyにlatex_template_nameがあるのを取り除き、GenerateLatexSubgraphRequestBodyだけがもつ様に変更する
class GenerateLatexSubgraphRequestBody(BaseModel):
    references_bib: str
    paper_content: PaperContent
    latex_template_name: LATEX_TEMPLATE_NAME = "mdpi"
    llm_mapping: GenerateLatexLLMMapping | None = None


class GenerateLatexSubgraphResponseBody(BaseModel):
    latex_text: str
    execution_time: dict[str, list[float]]


class PushLatexSubgraphRequestBody(BaseModel):
    github_config: GitHubConfig
    latex_text: str
    latex_template_name: LATEX_TEMPLATE_NAME = "mdpi"


class PushLatexSubgraphResponseBody(BaseModel):
    is_upload_successful: bool
    is_images_prepared: bool
    execution_time: dict[str, list[float]]


class CompileLatexSubgraphRequestBody(BaseModel):
    github_config: GitHubConfig
    latex_template_name: LATEX_TEMPLATE_NAME = "mdpi"
    llm_mapping: CompileLatexLLMMapping | None = None


class CompileLatexSubgraphResponseBody(BaseModel):
    compile_latex_dispatched: bool
    paper_url: str | None
    execution_time: dict[str, list[float]]
