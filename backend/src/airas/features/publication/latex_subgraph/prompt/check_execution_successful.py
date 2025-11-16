check_execution_successful_prompt = """\
You are highly proficient in writing LaTeX. Based on the following instructions, please determine whether the LaTeX processing was successful.

# Instructions：
- The section labeled "# LaTeX Text" contains the LaTeX content that was processed.
- The section labeled "# Error/Log" contains error messages or validation results from LaTeX processing (could be from compilation, chktex validation, or other LaTeX tools).
- Carefully read the LaTeX content and review the error messages/logs to determine whether the processing was successful.
- Consider both compilation errors (e.g., undefined commands, missing packages) and validation warnings (e.g., chktex style warnings) when determining success.

# LaTeX Text:
{{ latex_text }}

# Error/Log:
{{ latex_error_text }}"""
