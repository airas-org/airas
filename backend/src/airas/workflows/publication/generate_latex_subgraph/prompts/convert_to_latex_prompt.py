convert_to_latex_prompt = r"""
You are a LaTeX expert.
Your task is to convert each section of a research paper into plain LaTeX **content only**, without including any section titles or metadata.

Below are the paper sections. For each one, convert only the **content** into LaTeX:
{% for section in sections %}
---
Section: {{ section.name }}

{{ section.content }}

---
{% endfor %}

## LaTeX Formatting Rules:
- Use \\subsection{...} for any subsections within this section.
    - Subsection titles should be distinct from the section name;
    - Do not use '\\subsection{ {{ section }} }', or other slight variations. Use more descriptive and unique titles.
    - Avoid excessive subdivision. If a subsection is brief or overlaps significantly with another, consider merging them for clarity and flow.

- For listing contributions, use the LaTeX \\begin{itemize}...\\end{itemize} format.
    - Each item should start with a short title in \\textbf{...} format.
    - Avoid using -, *, or other Markdown bullet styles.

- **Mathematical expressions**:
    - All mathematical variables, symbols, operators, and expressions MUST be enclosed in inline math delimiters `$...$` or display math `\\[...\\]`.
    - Group related mathematical symbols into a single `$...$` block. Do NOT wrap each symbol in its own separate `$...$`.
        - Correct: `with probability at least $1 - \\delta$`
        - Wrong: `with probability at least 1 - \\ensuremath{\\delta}`
        - Wrong: `with probability at least $1$ - $\\delta$`
    - Subscripts (`_`) and superscripts (`^`) MUST always be inside math mode.
        - Correct: `the coefficient $\\eta_t$`
        - Wrong: `the coefficient \\ensuremath{\\eta}_t`
    - Use `\\hat{s}` instead of `s_{\\text{hat}}` for hat notation.

- When including tables, use the `tabularx` environment with `\\textwidth` as the target width.
    - At least one column must use the `X` type to enable automatic width adjustment and line breaking.
    - Include `\\hline` at the top, after the header, and at the bottom. Avoid vertical lines unless necessary.
    - To left-align content in `X` columns, define `\\newcolumntype{Y}{>{\\raggedright\\arraybackslash}X}` using the `array` package.

- When writing pseudocode, use the `algorithm` and `algorithmicx` LaTeX environments.
    - Only include pseudocode in the `Method` section. Pseudocode is not allowed in any other sections.
    - Prefer the `\\begin{algorithmic}` environment using **lowercase commands** such as `\\State`, `\\For`, and `\\If`, to ensure compatibility and clean formatting.
    - Pseudocode must represent actual algorithms or procedures with clear logic. Do not use pseudocode to simply rephrase narrative descriptions or repeat what has already been explained in text.
        - Good Example:
        ```latex
        \\State Compute transformed tokens: \\(\\tilde{T} \\leftarrow W\\,T\\)
        \\State Update: \\(T_{new} \\leftarrow \\tilde{T} + \\mu\\,T_{prev}\\)
        ```
- **Figures and images**:
    - Figures and figure references are already converted to LaTeX before this step. Do NOT modify `\\begin{figure}` environments or `Figure~\\ref{...}` references.
    - If any Pandoc figure syntax remains unconverted (e.g. `![Caption](images/file.pdf)` without a label), convert it to a LaTeX figure environment using `\\includegraphics[width=0.7\\linewidth]{...}` with an auto-generated label.

- **Escaping special characters**:
    - LaTeX special characters (`#`, `$`, `%`, `&`, `~`, `_`, `^`, `{`, `}`, `\\`) must be escaped with a leading backslash when they appear in plain text (e.g., `data\\_set`, `C\\&C`).
    - Underscores should be escaped (`\\_`) in plain text contexts, **but NOT in**:
        - Math mode (between `$...$` or `\\(...\\)`)
        - File paths (e.g., `images/memory_profiler.pdf`)
        - URLs and hyperlinks (e.g., `\\url{https://example.com/data_set}`)
        - Citation placeholders (e.g., `[vaswani_2017_attention]`)
        - Labels and Cross-references (e.g., `\\label{fig:result_v1}`, `\\ref{sec:method_approx}`)
        - Verbatim environments and Code blocks (e.g., `\\verb|int_x|`, `\\begin{lstlisting}...`)
    - Only escape underscores when they appear in regular narrative text outside these contexts.

- Always use ASCII hyphens (`-`) instead of en-dashes (`–`) or em-dashes (`—`) to avoid spacing issues in hyphenated terms.
- Do not include any of these higher-level commands such as \\documentclass{...}, \\begin{document}, and \\end{document}.
    - Additionally, avoid including section-specific commands such as \\begin{abstract}, \\section{ {{ section }} }, or any other similar environment definitions.
- Do not modify citation placeholders:
    - Citation placeholders appear in the format [citation_key], where citation_key contains underscores, numbers, and text (e.g., [vaswani_2017_attention], [smith_2023_deep]).
    - You must preserve these placeholders EXACTLY as they appear in the input text.
- If no LaTeX conversion is needed, output the content as-is without status messages like [Unchanged].
"""
