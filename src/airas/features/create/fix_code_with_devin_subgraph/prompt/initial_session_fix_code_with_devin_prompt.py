initial_session_fix_code_with_devin_prompt = """\
# Instruction
The error described in "# Error" occurred when executing main.py in the repository specified in "Repository URL" under the branch indicated in "Branch Name." Please modify the code and push the revised version to the remote repository.
Perform the modifications with reference to the rules specified in "# Rules."

Additionally, "# Information" contains details about the implemented code.
Please ensure that the implementation enables experiments for the new method described in "## Current Research Method."

- Repository URL：{{ repository_url }}
- Branch Name：{{ branch_name }}

Do not create a new branch under any circumstances; commit the changes to the specified branch.

# Rules
- Fix all errors found in the error messages
- When executing the script, ensure that the following information is always printed to standard output.If there are multiple experiments, this standard output must be produced for each experiment.
    - Experiment details
    - Concrete numerical data
    - File path of the figure visualizing the experimental results
- Be sure to perform a test run and confirm that it executes successfully. The test run should be designed to complete within a short execution time.
- If the deep learning models or datasets being used are unavailable, please select alternatives from "External Resources" and implement them.
- If similar errors appear in the Previous Error History, consider alternative approaches rather than repeating the same fixes
- Update pyproject.toml if new packages needed
- MANDATORY: You must update paths before saving. The following paths are required:
    - Image paths: .research/iteration{{ experiment_iteration }}/images (modify any existing image save paths to use this exact directory)
    - JSON paths: .research/iteration{{ experiment_iteration }}/ (Save each experiment's results as separate JSON files in this directory and print each JSON contents to standard output for verification)

# Error:
{{ new_method.experimental_results.error }}

# Standard output:
{{ new_method.experimental_results.result }}

# Previous Error History (for reference - avoid repeating same fixes)
{% if error_list %}
{% for error in error_list %}
### {{ loop.index }}. {{ error }}
{% endfor %}
{% endif %}

# Information

## Experimental Environment
{{ runner_type_prompt }}

## Current Research Method:
{{ new_method.method }}

## Experiment Details:
{{ new_method.experimental_design.experiment_details }}

## External Resources:
{{ new_method.experimental_design.external_resources }}"""
