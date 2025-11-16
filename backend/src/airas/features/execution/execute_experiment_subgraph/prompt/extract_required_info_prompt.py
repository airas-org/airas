extract_required_info_prompt = """\
The Python standard output and errors are provided below.
Extract all information related to the experimental results from the standard output, and extract the Python error details from the errors, outputting them exactly as they are without any modifications.
Do not extract unnecessary execution logs or information about Python package installations.

# Standard Output
{{ output_text_data }}

# Error
{{ error_text_data }}"""
