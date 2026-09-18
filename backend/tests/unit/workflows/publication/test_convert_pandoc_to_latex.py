"""An unknown citation key used to vanish from the paper without a word;
it is kept now, so the gate can name it."""

from airas.core.types.paper import PaperContent
from airas.workflows.publication.generate_latex_subgraph.nodes.convert_pandoc_to_latex import (
    convert_pandoc_to_latex,
)

BIB = """
@article{vaswani-2017-attention,
  title = {Attention Is All You Need},
  author = {Vaswani, Ashish},
  year = {2017}
}
"""


def _content(introduction: str) -> PaperContent:
    return PaperContent(
        title="t",
        abstract="a",
        introduction=introduction,
        related_work="r",
        background="b",
        method="m",
        experimental_setup="e",
        results="s",
        conclusion="c",
    )


def test_a_passage_locator_becomes_the_optional_argument() -> None:
    converted = convert_pandoc_to_latex(
        _content("Dropout helps [@vaswani-2017-attention, s1.p2]."), BIB
    )
    assert (
        converted.introduction == r"Dropout helps \cite[s1.p2]{vaswani-2017-attention}."
    )


def test_an_unknown_key_is_kept_so_the_gate_can_see_it() -> None:
    converted = convert_pandoc_to_latex(_content("As shown [@made-up-2020-key]."), BIB)
    assert converted.introduction == r"As shown \cite{made-up-2020-key}."
