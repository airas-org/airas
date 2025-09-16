convert_code_to_scripts_prompt = """
You are a machine learning researcher with strong development skills, tasked with refactoring a single, complete experimental script into a structured multi-file project.
The “Experiment Code” section contains a finished, runnable script. Your task is to **split this script into the separate files** as described in the "Instructions" and "Directory and Script Roles" sections.

# Instructions
- **Your primary task is to refactor the existing code, not to write new code from scratch.**
- You MUST extract the relevant logic from the "Experiment Code" section for each file. Do not introduce new logic or fall back to placeholder examples.
- Ensure that imports are correctly handled in each file.
- Full Experiment Production Readiness
  - Eliminate ALL placeholders, TODOs, dummy values, and synthetic data in configuration files
  - Use actual dataset names, real model parameters, and concrete hyperparameters from External Resources
  - Code logic should remain faithful to "Experiment Code" but configurations must be production-ready

- Error Prevention: While refactoring, proactively identify and fix potential runtime issues:
    - Environment compatibility: Ensure proper device/platform handling and resource availability checks.
    - Data type consistency: Verify compatible data types across operations and add necessary type conversions.
    - Dimension compatibility: Check tensor/array shapes and add reshaping operations where needed.
    - Import dependencies: Verify all required libraries are properly imported and available.
    - Dependency resolution: Ensure pyproject.toml has proper dependency ordering to avoid circular dependencies.
    - Error handling: Add appropriate try-catch blocks for common failure points like file I/O and model operations.
{% if secret_names %}
    - Environment Variables: The following environment variables are available for use: {{ secret_names|join(', ') }}. Use os.getenv() to access them in your code.
{% endif %}

- Directory and Script Roles
    - .research/iteration{{ experiment_iteration }}/images...Please save all images output from the experiment in this directory.
    - .research/iteration{{ experiment_iteration }}/...Save each experiment's results as separate JSON files in this directory and print each JSON contents to standard output for verification.
    - config/...Create two configuration files:
        - smoke_test.yaml: Small-scale configuration for quick validation (reduced epochs like 1-2, smaller datasets, limited iterations)
        - full_experiment.yaml: Full-scale configuration for complete experimental runs
    - src/
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
- STRICT FILE CONSTRAINT: Only these 7 files exist (6 Python files + 2 config files) - never import or reference any other modules/files. If experiment code references missing modules (e.g., `src.models`), consolidate all functionality into the existing files.

## Command Line Execution Requirements
The generated main.py must support the following command patterns:
```bash
# Smoke test only
uv run python -m src.main --smoke-test

# Full experiment only
uv run python -m src.main --full-experiment
```

The main.py should:
1. Parse command line arguments using argparse
2. Load the appropriate config file based on the flag
3. Execute the experiment workflow accordingly
4. Handle both smoke test and full experiment modes properly

{% if file_static_validations %}
# ========================================
# STATIC VALIDATION RESULTS - FIX THESE ISSUES
# ========================================

## All Static Validation Issues:
{% for file_path, file_static_validation in file_static_validations.items() %}
{% if file_static_validation.errors %}
### Errors in {{ file_path }}:
{% for error in file_static_validation.errors %}
- {{ error }}
{% endfor %}
{% endif %}
{% if file_static_validation.warnings %}
### Warnings in {{ file_path }}:
{% for warning in file_static_validation.warnings %}
- {{ warning }}
{% endfor %}
{% endif %}
{% endfor %}
{% endif %}

# Experimental Environment
{{ runner_type_prompt }}

# Current Research Method (Target for Experiment Design)
{{ new_method.method }}

# Experimental Design
- Strategy: {{ new_method.experimental_design.experiment_strategy }}
- Details: {{ new_method.experimental_design.experiment_details }}

{% if new_method.experimental_design.external_resources %}
# External Resources
{{ new_method.experimental_design.external_resources }}
{% endif %}

# Experiment Code
# This is the source script you must split into the file structure above.
{{ experiment_code_str }}"""
