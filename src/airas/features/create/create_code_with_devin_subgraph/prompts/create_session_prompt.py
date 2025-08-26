create_session_prompt = """# Instructions

The "New Method" and "Experiment Code" sections contain ideas for new machine learning research and the code associated with those ideas.
Please follow the "Rules" section to create an experimental script to conduct this research.

# Rules

- Please clone the repository specified in "Repository URL".
- Implement the changes in the branch specified in "Branch Name" in that repository and commit the changes.
- Do not create a new branch under any circumstances.

## Repository URL
{{ repository_url }}

## Branch Name
{{ branch_name }}

- Please create code that can run on NVIDIA Tesla T4 · 16 GB VRAM.
- After committing all changes, set "status_enum" to "stopped".
- Experimental scripts should be given a simple test run to make sure they work. The test run should not be too long.
- Install and use the necessary python packages as needed.
- Please also list the python packages required for the experiment in the requirements.txt file.
- All figures and plots (e.g., accuracy curves, loss plots, confusion matrix) must be saved in high-quality PDF format suitable for academic papers.
- Generate visualizations to verify experimental results and comparisons where applicable.
- The roles of directories and scripts are listed below. Follow the roles to complete your implementation.

## Directory and Script Roles

- `.github/workflows/run_experiment.yml` - Under no circumstances should the contents or folder structure of the "run_experiment.yml" file be altered. This rule must be observed.
- `.research/research_history.json` - Under no circumstances should the contents or folder structure of the "research_history.json" file be altered. This rule must be observed.
- `.research/iteration{{ experiment_iteration }}/images` - Please save all images output from the experiment in this directory.
- `config/` - If you want to set parameters for running the experiment, place the file that completes the parameters under this directory.
- `data/` - This directory is used to store data used for model training and evaluation.
- `models/` - This directory is used to store pre-trained and trained models.
- `src/` - Source code directory containing:
  - `train.py` - Scripts for training models. Implement the code to train the models.
  - `evaluate.py` - Script to evaluate the model. Implement the code to evaluate the model.
  - `preprocess.py` - Script for preprocessing data. Implement the code necessary for data preprocessing.
  - `main.py` - Scripts for running the experiment, using train.py, evaluate.py, and preprocess.py to implement the entire process from model training to evaluation.
    The script should be implemented in such a way that the results of the experiment can be seen in detail on the standard output.
- `requirements.txt` - Please list the python packages required to run the model.

# New Method
----------------------------------------
{{ new_method }}
----------------------------------------

# Experiment Code
----------------------------------------
{{ experiment_code }}
"""
