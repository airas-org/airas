import os
import re
from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.features.publication.latex_subgraph.prompt.check_figures_prompt import (
    check_figures_prompt,
)
from airas.features.publication.latex_subgraph.prompt.check_references_prompt import (
    check_references_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    latex_text: str


def embed_in_latex_template(
    latex_content: dict[str, str],
    latex_template_text: str,
    references_bib: str,
    figures_name: list[str],
    llm_name: LLM_MODEL,
    max_iterations: int = 5,
) -> str:
    latex_text = _fill_template(latex_content, latex_template_text)

    for i in range(max_iterations):
        logger.info(f"Iteration {i + 1} of {max_iterations}")
        updated = latex_text
        updated = _check_references(llm_name, updated, references_bib)
        updated = _check_figures(llm_name, updated, figures_name)
        # updated = _check_duplicates(
        #     updated,
        #     {
        #         "figure": r"\\includegraphics.*?{(.*?)}",
        #         "section header": r"\\section{([^}]*)}",
        #     },
        # )
        # updated = self._fix_latex_errors(updated)

        if updated == latex_text:
            logger.info("All checks complete.")
            break
        latex_text = updated
    else:
        logger.warning("Max iterations reached.")

    return latex_text


def _fill_template(content: dict, latex_template: str) -> str:
    for section, value in content.items():
        placeholder = f"{section.upper()} HERE"
        latex_template = latex_template.replace(placeholder, value)
    return latex_template


def _check_references(llm_name: LLM_MODEL, latex_text: str, references_bib: str) -> str:
    client = LLMFacadeClient(llm_name)
    env = Environment()

    cites = re.findall(r"\\cite[a-z]*{([^}]*)}", latex_text)

    missing_cites = [cite for cite in cites if cite.strip() not in references_bib]

    if not missing_cites:
        logger.info("Reference check passed.")
        return latex_text

    logger.info(f"Missing references found: {missing_cites}")

    data = {
        "latex_text": latex_text,
        "references_bib": references_bib,
        "missing_cites": missing_cites,
    }
    template = env.from_string(check_references_prompt)
    messages = template.render(data)
    output, cost = client.structured_outputs(
        message=messages,
        data_model=LLMOutput,
    )
    if output is None:
        raise RuntimeError(
            f"LLM failed to respond for missing references: {missing_cites}"
        )
    return output["latex_text"]


def _check_figures(
    llm_name: LLM_MODEL,
    latex_text: str,
    figures_name: list[str],
    pattern: str = r"\\includegraphics.*?{(.*?)}",
) -> str:
    client = LLMFacadeClient(llm_name)
    env = Environment()
    referenced_paths = re.findall(pattern, latex_text)
    referenced_figs = [os.path.basename(path) for path in referenced_paths]

    fig_to_use = [fig for fig in referenced_figs if fig in figures_name]

    if not fig_to_use:
        logger.info("No figures referenced in the LaTeX document.")
        return latex_text

    env = Environment()
    data = {
        "latex_text": latex_text,
        "fig_to_use": fig_to_use,
    }
    template = env.from_string(check_figures_prompt)
    messages = template.render(data)
    output, cost = client.structured_outputs(
        message=messages,
        data_model=LLMOutput,
    )
    if output is None:
        raise RuntimeError(f"LLM failed to respond for figures: {fig_to_use}")
    return output["latex_text"]


# def _check_duplicates(self, tex_text: str, patterns: dict[str, str]) -> str:
#     for element_type, pattern in patterns.items():
#         items = re.findall(pattern, tex_text)
#         duplicates = {x for x in items if items.count(x) > 1}
#         if duplicates:
#             logger.info(f"Duplicate {element_type} found: {duplicates}.")
#             prompt = f"""\
# # LaTeX text
# --------
# {tex_text}
# --------
# Duplicate {element_type} found: {", ".join(duplicates)}. Ensure any {element_type} is only included once.
# If duplicated, identify the best location for the {element_type} and remove any other.
# Return the complete corrected LaTeX text with the duplicates fixed."""
#             tex_text = self._call_llm(prompt) or tex_text
#     return tex_text


# class LatexNode:
#     def __init__(
#         self,
#         llm_name: LLM_MODEL,
#         save_dir: str,
#         pdf_file_name: str = "generated_paper.pdf",
#         template_file_name: str = "template.tex",
#         max_iterations: int = 5,
#         timeout: int = 30,
#         client: LLMFacadeClient | None = None,
#     ):
#         self.llm_name = llm_name
#         self.save_dir = save_dir

#         )

#     def _call_llm(self, prompt: str) -> str | None:
#         system_prompt = """
# You are a helpful LaTeX rewriting assistant.
# The value of \"latex_full_text\" must contain the complete LaTeX text."""
#         messages = system_prompt + prompt
#         try:
#             output, cost = self.client.structured_outputs(
#                 message=messages,
#                 data_model=LLMOutput,
#             )
#             return output["latex_full_text"]
#         except Exception as e:
#             logger.error(f"Error: No response from LLM in _call_llm: {e}")
#             return None

# def _fill_template(self, content: dict) -> str:
#     with open(self.latex_instance_file, "r") as f:
#         tex_text = f.read()

#     for section, value in content.items():
#         placeholder = f"{section.upper()} HERE"
#         tex_text = tex_text.replace(placeholder, value)
#     with open(self.latex_instance_file, "w") as f:
#         f.write(tex_text)
#     return tex_text

# def _write_references_bib(self, references_bib: dict[str, str]):
#     bib_file_path = os.path.join(self.save_dir, "references.bib")
#     try:
#         with open(bib_file_path, "a", encoding="utf-8") as f:
#             for entry in references_bib.values():
#                 f.write("\n\n" + entry.strip())
#         logger.info(
#             f"Wrote {len(references_bib)} BibTeX entries to {bib_file_path}"
#         )
#     except Exception as e:
#         logger.error(f"Failed to write references.bib: {e}")

#     def _check_references(self, tex_text: str) -> str:
#         cites = re.findall(r"\\cite[a-z]*{([^}]*)}", tex_text)
#         bib_path = os.path.join(self.save_dir, "references.bib")
#         if not os.path.exists(bib_path):
#             raise FileNotFoundError(f"references.bib file is missing at: {bib_path}")

#         with open(bib_path, "r") as f:
#             bib_text = f.read()
#         missing_cites = [cite for cite in cites if cite.strip() not in bib_text]

#         if not missing_cites:
#             logger.info("Reference check passed.")
#             return tex_text

#         logger.info(f"Missing references found: {missing_cites}")
#         prompt = f""""\n
# # LaTeX text
# --------
# {tex_text}
# --------
# # References.bib content
# --------
# {bib_text}
# --------
# The following reference is missing from references.bib: {missing_cites}.
# Only modify the BibTeX content or add missing \\cite{{...}} commands if needed.

# Do not remove, replace, or summarize any section of the LaTeX text such as Introduction, Method, or Results.
# Do not comment out or rewrite any parts. Just fix the missing references.
# Return the complete LaTeX document, including any bibtex changes."""
#         llm_response = self._call_llm(prompt)
#         if llm_response is None:
#             raise RuntimeError(
#                 f"LLM failed to respond for missing references: {missing_cites}"
#             )
#         return llm_response

#     def _check_figures(
#         self,
#         tex_text: str,
#         figures_name: list[str],
#         pattern: str = r"\\includegraphics.*?{(.*?)}",
#     ) -> str:
#         referenced_paths = re.findall(pattern, tex_text)
#         referenced_figs = [os.path.basename(path) for path in referenced_paths]

#         fig_to_use = [fig for fig in referenced_figs if fig in figures_name]

#         if not fig_to_use:
#             logger.info("No figures referenced in the LaTeX document.")
#             return tex_text

#         prompt = f"""\n
# # LaTeX Text
# --------
# {tex_text}
# --------
# # Available Images
# --------
# {fig_to_use}
# --------
# Please modify and output the above Latex text based on the following instructions.
# - Only “Available Images” are available.
# - If a figure is mentioned on Latex Text, please rewrite the content of Latex Text to cite it.
# - Do not use diagrams that do not exist in “Available Images”.
# - Return the complete LaTeX text."""

#         tex_text = self._call_llm(prompt) or tex_text
#         return tex_text

#     def _check_duplicates(self, tex_text: str, patterns: dict[str, str]) -> str:
#         for element_type, pattern in patterns.items():
#             items = re.findall(pattern, tex_text)
#             duplicates = {x for x in items if items.count(x) > 1}
#             if duplicates:
#                 logger.info(f"Duplicate {element_type} found: {duplicates}.")
#                 prompt = f"""\n
# # LaTeX text
# --------
# {tex_text}
# --------
# Duplicate {element_type} found: {", ".join(duplicates)}. Ensure any {element_type} is only included once.
# If duplicated, identify the best location for the {element_type} and remove any other.
# Return the complete corrected LaTeX text with the duplicates fixed."""
#                 tex_text = self._call_llm(prompt) or tex_text
#         return tex_text


#     def embed_in_latex_template(
#         self,
#         paper_tex_content: dict[str, str],
#         references_bib: dict[str, str],
#         figures_name: list[str],
#     ) -> str:
#         self._copy_template()
#         tex_text = self._fill_template(paper_tex_content)
#         self._write_references_bib(references_bib)

#         for i in range(self.max_iterations):
#             logger.info(f"=== Iteration {i + 1} ===")
#             updated = tex_text
#             updated = self._check_references(updated)
#             updated = self._check_figures(updated, figures_name)
#             updated = self._check_duplicates(
#                 updated,
#                 {
#                     "figure": r"\\includegraphics.*?{(.*?)}",
#                     "section header": r"\\section{([^}]*)}",
#                 },
#             )
#             # updated = self._fix_latex_errors(updated)

#             if updated == tex_text:
#                 logger.info("All checks complete.")
#                 break
#             tex_text = updated
#         else:
#             logger.warning("Max iterations reached.")

#         with open(self.latex_instance_file, "w") as f:
#             f.write(tex_text)

#         return tex_text


if __name__ == "__main__":
    llm_name = "o3-mini-2025-01-31"
    latex_content = {
        "abstract": "This is a sample abstract.",
        "introduction": "This is a sample introduction.",
        "method": "This is a sample method.",
        "results": "These are the sample results.",
        "conclusion": "This is a sample conclusion.",
    }

    references_bib = """\
@article{ref1,
title={Sample Reference},
author={Doe, John},
journal={Sample Journal},
year={2025}
}"""

    image_file_name_list = ["figure1.png", "figure2.jpg"]
    latex_template = r"""\
\PassOptionsToPackage{numbers}{natbib}
\documentclass{article} % For LaTeX2e
\usepackage{iclr2024_conference,times}

\usepackage[utf8]{inputenc} % allow utf-8 input
\usepackage[T1]{fontenc}    % use 8-bit T1 fonts
\usepackage{hyperref}       % hyperlinks
\usepackage{url}            % simple URL typesetting
\usepackage{booktabs}       % professional-quality tables
\usepackage{amsfonts}       % blackboard math symbols
\usepackage{nicefrac}       % compact symbols for 1/2, etc.
\usepackage{microtype}      % microtypography
\usepackage{titletoc}

\usepackage{subcaption}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{multirow}
\usepackage{color}
\usepackage{colortbl}
\usepackage{cleveref}
\usepackage{algorithm}
\usepackage{algorithmicx}
\usepackage{algpseudocode}
\usepackage{tikz}
\usepackage{pgfplots}
\usepackage{float}
\usepackage{array}
\usepackage{tabularx}
\pgfplotsset{compat=newest}

\DeclareMathOperator*{\argmin}{arg\,min}
\DeclareMathOperator*{\argmax}{arg\,max}

\graphicspath{{../}} % To reference your generated figures, see below.

\title{TITLE HERE}

\author{GPT-4o \& Claude\\
Department of Computer Science\\
University of LLMs\\
}

\newcommand{\fix}{\marginpar{FIX}}
\newcommand{\new}{\marginpar{NEW}}

\begin{document}

\maketitle

\begin{abstract}
This is a sample abstract.
\end{abstract}

\section{Introduction}
\label{sec:intro}

This is a sample introduction.

\begin{figure}[H]
\centering
\includegraphics[width=0.8\linewidth]{figure1.png}
\caption{Sample figure 1 in introduction.}
\end{figure}

\section{Related Work}
\label{sec:related}
RELATED WORK HERE

\section{Background}
\label{sec:background}
BACKGROUND HERE

\section{Method}
\label{sec:method}

This is a sample method section.

\begin{figure}[H]
\centering
\includegraphics[width=0.8\linewidth]{figure2.jpg}
\caption{Sample figure 2 in method.}
\end{figure}

% Removed figure that referenced an unavailable image (figure3.jpg).

\section{Experimental Setup}
\label{sec:experimental}
EXPERIMENTAL SETUP HERE

\section{Results}
\label{sec:results}

These are the sample results.

\section{Results}
More sample results here.

\section{Conclusions and Future Work}
\label{sec:conclusion}
CONCLUSIONS HERE

This work was generated by \textsc{AIRAS} \citep{airas2025}.

\bibliographystyle{iclr2024_conference}
\bibliography{references}

\end{document}
"""

    result = embed_in_latex_template(
        latex_content=latex_content,
        latex_template_text=latex_template,
        references_bib=references_bib,
        figures_name=image_file_name_list,
        llm_name=llm_name,
    )

    print(result)
