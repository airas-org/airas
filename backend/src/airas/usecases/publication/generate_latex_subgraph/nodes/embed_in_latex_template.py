from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.core.types.paper import PaperContent

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    latex_text: str


def embed_in_latex_template(
    latex_formatted_paper_content: PaperContent,
    latex_template_text: str,
) -> str:
    data = {
        "title": latex_formatted_paper_content.title,
        "abstract": latex_formatted_paper_content.abstract,
        "introduction": latex_formatted_paper_content.introduction,
        "related_work": latex_formatted_paper_content.related_work,
        "background": latex_formatted_paper_content.background,
        "method": latex_formatted_paper_content.method,
        "experimental_setup": latex_formatted_paper_content.experimental_setup,
        "results": latex_formatted_paper_content.results,
        "conclusion": latex_formatted_paper_content.conclusion,
    }

    env = Environment(
        variable_start_string="<<",
        variable_end_string=">>",
        block_start_string="<%",
        block_end_string="%>",
    )
    template = env.from_string(latex_template_text)
    latex_text = template.render(data)
    return latex_text
