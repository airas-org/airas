is_execution_successful_prompt = """\
You are highly proficient in writing LaTeX. Based on the following instructions, please determine whether the LaTeX compilation was successful.

# Instructions：
- The section labeled “# LaTeX Text” contains the LaTeX content that was compiled, and the section labeled “# Error” contains the error messages output during compilation.
- Carefully read the LaTeX content and review the error messages to determine whether the compilation was successful.

# Latex Text:
{{ latex_text }}

# Error:
{{ latex_error_text }}"""
