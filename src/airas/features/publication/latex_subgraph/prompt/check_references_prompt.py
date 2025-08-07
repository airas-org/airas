check_references_prompt = """"\
# LaTeX text
--------
{{ latex_text }}
--------
# References.bib content
--------
{{ references_bib }}
--------
The following reference is missing from references.bib: {{ missing_cites }} .
Only modify the BibTeX content or add missing \\cite{...} commands if needed.

Do not remove, replace, or summarize any section of the LaTeX text such as Introduction, Method, or Results.
Do not comment out or rewrite any parts. Just fix the missing references.
Return the complete LaTeX document, including any bibtex changes."""
