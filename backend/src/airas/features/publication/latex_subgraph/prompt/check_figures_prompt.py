check_figures_prompt = """\
# LaTeX Text
--------
{{ latex_text }}
--------
# Available Images
--------
{{ fig_to_use }}
--------
Please modify and output the above Latex text based on the following instructions.
- Only “Available Images” are available.
- If a figure is mentioned on Latex Text, please rewrite the content of Latex Text to cite it.
- Do not use diagrams that do not exist in “Available Images”.
- Return the complete LaTeX text."""
