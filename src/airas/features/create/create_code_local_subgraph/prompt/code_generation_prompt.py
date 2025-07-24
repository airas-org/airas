code_generation_prompt = """\
# Instructions
The "New Method" and "Experiment Code" sections contain ideas for new machine learning research and the code associated with those ideas.
Please follow the "Rules" section to create experimental scripts to conduct this research.

# Rules
- Please create code that can run on NVIDIA Tesla T4 · 16 GB VRAM.
- Experimental scripts should be given a simple test run to make sure they work.
- Install and use the necessary python packages as needed.
- Please also list the python packages required for the experiment in the requirements.txt file.
- All figures and plots must be saved in high-quality PDF format suitable for academic papers.

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
{{ experiment_code }}

# Output Format
Please provide the code for each file in the following JSON format:

{
    "src/train.py": "# Training script code here...",
    "src/evaluate.py": "# Evaluation script code here...",
    "src/preprocess.py": "# Preprocessing script code here...",
    "src/main.py": "# Main experiment script code here...",
    "requirements.txt": "# Required packages list here...",
    "config/config.yaml": "# Configuration file content here..."
}

Make sure each file contains complete, functional code that follows the requirements above.
"""
