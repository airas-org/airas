retrieve_code_with_devin_prompt = """\
# Instructions
The GitHub repository provided in the "GitHub Repository URL" corresponds to the implementation used in the research described in "Description of Methodology". Please extract the information according to the following rules.
# Rules
- If a machine learning model is used in the implementation, extract its details and the relevant code.
- If a dataset is used in the implementation, extract its details and the relevant code.
- If there are configuration files for experiments, extract all their contents.
- If there is an implementation corresponding to the "Description of Methodology", extract its details.
- If there is information about required Python packages, extract that information.
- If there is information related to the experiments in files such as README.md, extract that information.
- The extracted information should be made available as `extracted_info`.

# Output Format
Please provide the extracted information in the following structured format:
```json
"structured_output": {
    "extracted_info": "<Extracted information>"
}
```

# Description of Methodology
{{ base_method_text }}
# GitHub Repository URL
{{ github_url }}"""
