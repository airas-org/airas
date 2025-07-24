code_fix_prompt = """\
# Instructions
You are tasked with fixing Python code that failed during execution. Analyze the error messages and output data to identify and fix the issues in the provided files.

# Rules
- Fix all errors found in the error messages
- Ensure the code can run on NVIDIA Tesla T4 · 16 GB VRAM
- Make minimal changes to preserve the original functionality
- Update requirements.txt if new packages are needed
- Ensure all imports are correct and available
- Fix any syntax errors, import errors, or runtime errors
- Make sure the code follows Python best practices

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

{% endfor %}

# Output Format
Please provide the fixed code for each file that needs to be modified in the following JSON format:

{
    "file_path_1": "# Fixed code content here...",
    "file_path_2": "# Fixed code content here...",
    ...
}

Only include files that need to be modified. Provide the complete content for each file that needs changes.

# Analysis
First, analyze the errors:
1. Identify the root cause of each error
2. Determine which files need to be modified
3. Plan the fixes needed

Then provide the fixed files in the JSON format above.
"""
