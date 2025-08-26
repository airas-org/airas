code_fix_prompt = """\
# Instructions
You are tasked with fixing Python code that failed during execution. Analyze the error messages and output data to identify and fix the issues in the provided files.

# Rules
- Fix all errors found in the error messages
- If a file does not have any errors and does not need any changes, you MUST return the original content of the file exactly as provided, without any modifications, comments, or additional text like '[No changes]'.
- Ensure the code can run on NVIDIA Tesla T4 · 16 GB VRAM
- Make minimal changes to preserve the original functionality
- Update requirements.txt if new packages are needed
- Ensure all imports are correct and available
- Fix any syntax errors, import errors, or runtime errors
- Make sure the code follows Python best practices
- Please modify it so that all images output from the experiment are saved in this directory.
  - .research/iteration{{ experiment_iteration }}/images

# Error Information
## Output Data:
{{ output_text_data }}

## Error Data:
{{ error_text_data }}

# Current Files
{% for file_path, content in current_files.items() %}
## {{ file_path }}
```python
{{ content }}
```

{% endfor %}"""
