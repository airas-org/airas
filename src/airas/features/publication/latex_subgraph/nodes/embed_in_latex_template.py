from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.types.paper import PaperContent

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


if __name__ == "__main__":
    latex_formatted_paper_content = PaperContent(
        title="Sample Paper Title",
        abstract="This is a sample abstract.",
        introduction="This is a sample introduction.",
        related_work="This is a sample related work.",
        background="This is a sample background.",
        method="This is a sample method.",
        experimental_setup="This is a sample experimental setup.",
        results="These are the sample results.",
        conclusion="This is a sample conclusion.",
    )

    latex_template = r"""\
\documentclass{article}

\usepackage{agents4science_2025}
% to compile a preprint version, e.g., for submission to arXiv, add the
% \usepackage[preprint]{agents4science_2025}

% to compile a camera-ready version, add the [final] option, e.g.:
% \usepackage[final]{agents4science_2025}

% For workshops, the authors should use the workshop options and add the name of the workshop.
% The "\workshoptitle" command is used to set the workshop title.
%
% \usepackage[sglblindworkshop]{agents4science_2025}
% \workshoptitle{WORKSHOP TITLE}


\usepackage[utf8]{inputenc} % allow utf-8 input
\usepackage[T1]{fontenc}    % use 8-bit T1 fonts
\usepackage{hyperref}       % hyperlinks
\usepackage{url}            % simple URL typesetting
\usepackage{booktabs}       % professional-quality tables
\usepackage{amsfonts}       % blackboard math symbols
\usepackage{nicefrac}
\usepackage{microtype}
\usepackage{xcolor}


\title{<< title >>}


% The \author macro works with any number of authors. There are two commands
% used to separate the names and addresses of multiple authors: \And and \AND.
%
% Using \And between authors leaves it to LaTeX to determine where to break the
% lines. Using \AND forces a line break at that point. So, if LaTeX puts 3 of 4
% authors names on the first line, and the last on the second line, try using
% \AND instead of \And before the third author name.


\author{%
  David S.~Hippocampus\thanks{Use footnote for providing further information
    about author (webpage, alternative address)---\emph{not} for acknowledging
    funding agencies.} \\
  Department of Computer Science\\
  Cranberry-Lemon University\\
  Pittsburgh, PA 15213 \\
  \texttt{hippo@cs.cranberry-lemon.edu} \\
  % examples of more authors
  % \And
  % Coauthor \\
  % Affiliation \\
  % Address \\
  % \texttt{email} \\
  % \AND
  % Coauthor \\
  % Affiliation \\
  % Address \\
  % \texttt{email} \\
  % \And
  % Coauthor \\
  % Affiliation \\
  % Address \\
  % \texttt{email} \\
  % \And
  % Coauthor \\
  % Affiliation \\
  % Address \\
  % \texttt{email} \\
}


\begin{document}


\maketitle


\begin{abstract}
<< abstract >>
\end{abstract}



\section{Introduction}
<< introduction >>

\section{Related Work}
<< related_work >>

\section{Background}
<< background >>

\section{Method}
<< method >>

\section{Experimental Setup}
<< experimental_setup >>

\section{Results}
<< results >>

\section{Conclusion}
<< conclusion >>


\bibliographystyle{plainnat}
\bibliography{references}

\end{document}
"""

    result = embed_in_latex_template(
        latex_formatted_paper_content=latex_formatted_paper_content,
        latex_template_text=latex_template,
    )

    print(result)
