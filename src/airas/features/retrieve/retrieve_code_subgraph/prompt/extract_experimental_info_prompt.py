extract_experimental_info_prompt = """\
You are a researcher in machine learning with expertise in engineering.
# Instruction
The content described in "Repository Content" corresponds to the GitHub repository of the method described in "Method."
Please extract the code related to the "Method" and output it as `experimental_code`.
Also, extract the experimental settings related to the "Method" and output them as `experimental_code`.
## Method
{{ method_text }}
## Repository Content
{{ repository_content_str }}"""
