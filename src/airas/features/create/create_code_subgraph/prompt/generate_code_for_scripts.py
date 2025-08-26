generate_code_for_scripts_prompt = """\n# Instructions
The "New Method" and "Experiment Code" sections contain ideas for new machine learning research and the code associated with those ideas.
Please follow the "Rules" section to create experimental scripts to conduct this research.

# Rules
- Please create code that can run on NVIDIA Tesla T4 · 16 GB VRAM.
- Experimental scripts should be given a simple test run to make sure they work.
- **Imports and Dependencies:**
    - Inside the `src` directory, always use relative imports (e.g., `from .train import ...`).
    - Ensure every imported package is listed in `requirements.txt`.
- All figures and plots must be saved in high-quality PDF format suitable for academic papers.
- Generate visualizations to verify experimental results and comparisons where applicable.

## Directory and Script Roles
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

# New Method
----------------------------------------
{{ new_method }}
----------------------------------------
# Experiment Code
----------------------------------------
{{ experiment_code }}"""
