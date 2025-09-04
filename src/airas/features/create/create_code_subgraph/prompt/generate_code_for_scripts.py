generate_code_for_scripts_prompt = """
You are a machine learning researcher with strong development skills, tasked with refactoring a single, complete experimental script into a structured multi-file project.
The “Experiment Code” section contains a finished, runnable script. Your task is to **split this script into the separate files** as described in the "Instructions" and "Directory and Script Roles" sections.

# Instructions
- **Your primary task is to refactor the existing code, not to write new code from scratch.**
- You MUST extract the relevant logic from the "Experiment Code" section for each file. Do not introduce new logic or fall back to placeholder examples.
- Ensure that imports are correctly handled in each file.

- Error Prevention: While refactoring, proactively identify and fix potential runtime issues:
    - **Environment compatibility**: Ensure proper device/platform handling and resource availability checks.
    - **Data type consistency**: Verify compatible data types across operations and add necessary type conversions.
    - **Dimension compatibility**: Check tensor/array shapes and add reshaping operations where needed.
    - **Import dependencies**: Verify all required libraries are properly imported and available.
    - **Dependency resolution**: Ensure requirements.txt has proper dependency ordering to avoid circular dependencies and compatible version constraints (e.g., torch>=1.13.0,<2.0.0, torchdata>=0.5.0,<0.8.0, dgl>=1.1.0,<2.0.0).
    - **Error handling**: Add appropriate try-catch blocks for common failure points like file I/O and model operations.

- Directory and Script Roles
    - .research/iteration{{ experiment_iteration }}/images...Please save all images output from the experiment in this directory.
    - config...Extract dataset URLs, model specifications, hyperparameters, and experiment settings.
    - data...This directory is used to store data used for model training and evaluation.
    - models...This directory is used to store pre-trained and trained models.
    - src
        - train.py...Extract all functions and classes related to model.
        - evaluate.py...Extract all functions and classes related to model evaluation, statistical analysis, and plotting.
        - preprocess.py...Extract any data loading or preprocessing logic.
        - main.py...Create the main execution script using relative imports (e.g., `from .train import ...`) to orchestrate the experimental workflow. Load configuration from `config/config.yaml` using PyYAML.
    - requirements.txt...Analyze the "Experiment Code" header and import statements. List all required Python packages here, one per line.

# Experimental Environment
{{ runtime_prompt }}

# New Method
{{ new_method.method }}

# Experiment Code
# This is the source script you must split into the file structure above.
{{ new_method.experimental_design.experiment_code }}
"""
