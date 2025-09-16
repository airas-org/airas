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
-The following files used in the experiment are listed along with their descriptions. Under no circumstances should you modify any files other than these or add new files.
    - config...Create two configuration files:
        - smoke_test.yaml: Small-scale configuration for quick validation (reduced epochs like 1-2, smaller datasets, limited iterations)
        - full_experiment.yaml: Full-scale configuration for complete experimental runs
    - data...This directory is used to store data used for model training and evaluation.
    - models...This directory is used to store pre-trained and trained models.
    - src
        - train.py...Extract all functions and classes related to model.
        - evaluate.py...Extract all functions and classes related to model evaluation, statistical analysis, and plotting. Please implement the code so that the evaluation results are always output to standard output.
        - preprocess.py...Extract any data loading or preprocessing logic.
        - main.py...Create the main execution script with command-line argument support:
            - Please make sure to always create main.py.
            - Add argparse to handle --smoke-test and --full-experiment flags
            - Load appropriate config file based on the flag (smoke_test.yaml or full_experiment.yaml)
            - Use relative imports (e.g., `from .train import ...`) to orchestrate the experimental workflow
            - Implement two-phase execution: smoke test first, then full experiment if smoke test passes
            - Use PyYAML for configuration loading
    - pyproject.toml...Analyze the "Experiment Code" header and import statements. Configure the project dependencies and package information in TOML format.
                        Dependencies must be an array format like `dependencies = ["numpy>=1.21.0", "torch>=1.9.0"]`, NOT a mapping format like `[project.dependencies]` with key-value pairs.
- When executing the script, ensure that the following information is always printed to standard output.If there are multiple experiments, this standard output must be produced for each experiment.
    - Experiment details
    - Concrete numerical data
    - File path of the figure visualizing the experimental results
- Be sure to perform a test run and confirm that it executes successfully. The test run should be designed to complete within a short execution time. Implement the test execution so that it can be run as a smoke test.
- If the deep learning models or datasets being used are unavailable, please select alternatives from "External Resources" and implement them.
- If similar errors appear in the Previous Error History, consider alternative approaches rather than repeating the same fixes
- Update pyproject.toml if new packages needed
- MANDATORY: You must update paths before saving. The following paths are required:
    - Image paths: .research/iteration{{ experiment_iteration }}/images (modify any existing image save paths to use this exact directory)
    - JSON paths: .research/iteration{{ experiment_iteration }}/ (Save each experiment's results as separate JSON files in this directory and print each JSON contents to standard output for verification)
    - Do not push the .research/iteration{{ experiment_iteration }}/ directory containing the test execution results to the remote repository; only update the implementation paths.

## Command Line Execution Requirements
The generated main.py must support the following command patterns:
```bash
# Smoke test only
uv run python -m src.main --smoke-test

# Full experiment only
uv run python -m src.main --full-experiment
```

# Error:
{{ new_method.experimental_results.error }}

# Standard output:
{{ new_method.experimental_results.result }}

# Information

## Experimental Environment
{{ runner_type_prompt }}

## Current Research Method:
{{ new_method.method }}

## Experiment Details:
{{ new_method.experimental_design.experiment_details }}

## External Resources:
{{ huggingface_data }}"""
