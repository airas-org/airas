fix_latex_text_prompt = """\
You are highly proficient in writing LaTeX. Based on the following instructions, please revise the LaTeX content accordingly.

# Instructions:
- The section labeled "# LaTeX Text" contains the LaTeX content that was processed.
- The section labeled "# Error/Log" contains error messages or validation results from LaTeX processing (could be from compilation errors, chktex validation warnings, or other LaTeX tools).
- Carefully read the error messages/logs and identify the necessary corrections in the LaTeX content:
  - For compilation errors: Fix syntax errors, missing packages, undefined commands, etc.
  - For chktex warnings: Address LaTeX style issues, improper formatting, spacing problems, etc.
  - For combined logs: Address all issues mentioned across different validation stages.
- Please output the entire corrected LaTeX content after applying all necessary fixes.

# LaTeX Text:
{{ latex_text }}

# Error/Log:
{{ latex_error_text }}"""
