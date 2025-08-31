generate_code_for_scripts_prompt = """\
You are a machine learning researcher with strong development skills.
The “New Method” and “Experiment Code” sections contain ideas for new machine learning research and the associated code. Please implement runnable code based on “Experiment Code” in accordance with the directions in “Instructions.”

# Instructions
- The experiment is run from the project root using the command `python -m src.main`.
- Imports and Dependencies:
    - Inside the `src` directory, always use relative imports (e.g., `from .train import ...`).
    - Ensure every imported package is listed in `requirements.txt`.
- All figures and plots must be saved in high-quality PDF format suitable for academic papers.
- Generate visualizations to verify experimental results and comparisons where applicable.
- **File Scope:** Only generate or modify the files explicitly listed in the 'Directory and Script Roles' section. Do not create, modify, or assume the existence of any other files.
- Directory and Script Roles
    - .research/iteration{{ experiment_iteration }}/images...Please save all images output from the experiment in this directory.
    - config...If you want to set parameters for running the experiment, place the file that completes the parameters under this directory.
    - data...This directory is used to store data used for model training and evaluation.
    - models...This directory is used to store pre-trained and trained models.
    - src
        - train.py...Scripts for training models. Implement the code to train the models.
        - evaluate.py...Script to evaluate the model. Implement the code to evaluate the model.
        - preprocess.py...Script for preprocessing data. Implement the code necessary for data preprocessing.
        - main.py...Scripts for running the experiment, using train.py, evaluate.py, and preprocess.py to implement the entire process from model training to evaluation.
                    The script should be implemented in such a way that the results of the experiment can be seen in detail on the standard output.
    - requirements.txt...Please list the python packages required to run the model.

# Experimental Environment
{{ runtime_prompt }}

# New Method
{{ new_method }}

# Experiment Code
{{ experiment_code }}"""
