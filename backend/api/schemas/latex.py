from pydantic import BaseModel

from airas.types.latex import LATEX_TEMPLATE_NAME
from airas.types.paper import PaperContent


class GenerateLatexSubgraphRequestBody(BaseModel):
    references_bib: str
    paper_content: PaperContent
    latex_template_name: LATEX_TEMPLATE_NAME = "iclr2024"


class GenerateLatexSubgraphResponseBody(BaseModel):
    latex_text: str
    execution_time: dict[str, list[float]]
