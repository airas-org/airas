extract_experimental_info_prompt = """\
You are a researcher with expertise in engineering in the field of machine learning.

# Instructions
- The content described in “Repository Content” corresponds to the GitHub repository of the method described in “Method.”
- Please extract the following two pieces of information from “Repository Content”:
    - experimental_code：Extract the implementation sections that are directly related to the method described in “Method.”
    - experimental_info：Extract and output the experimental settings related to the method described in “Method.”

# Method
{{ method_text }}

# Repository Content
{{ repository_content_str }}"""
