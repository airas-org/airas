fix_latex_text_prompt = """\
You are highly proficient in writing LaTeX. Based on the following instructions, please revise the LaTeX content accordingly.

# Instructions:
- The section labeled “# LaTeX Text” contains the LaTeX content that was compiled, and the section labeled “# Error” contains the error messages that were output during compilation.
- Carefully read the error messages, identify the necessary corrections in the LaTeX content, and revise them accordingly.
- Please output the entire LaTeX content after applying the corrections.

# LaTeX Text:
{{ latex_text }}

# Error:
{{ latex_error_text }}"""
