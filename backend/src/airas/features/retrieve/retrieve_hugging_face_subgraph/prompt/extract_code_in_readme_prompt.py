extract_code_in_readme_prompt = """\
From the Hugging Face README provided in “# README,” extract and output only the Python code required for execution. Do not output any other information. In particular, if no implementation method is described, output an empty string.

# README
{{ huggingface_readme}}
"""
