select_experimental_files_prompt = """\
You are a researcher with expertise in machine learning engineering.

# Instructions
- The "Repository Code Structure" section contains a summary of files from a GitHub repository associated with the paper described in "Paper Summary."
- Your task is to select the files that are most relevant to understanding the method and experimental settings described in the paper.
- Select files that contain:
    - Core implementation of the proposed method (models, algorithms, training loops)
    - Experimental configurations (hyperparameters, dataset settings, training settings)
    - Key utility functions directly related to the method

- Do NOT select:
    - Test files (test_*.py, *_test.py)
    - Documentation files unless they contain experimental settings
    - Generic utility files not specific to the method
    - Example or demo scripts unless they show the main experimental setup

# Paper Summary

## Main Contributions
{{ paper_summary.main_contributions }}

## Methodology
{{ paper_summary.methodology }}

## Experimental Setup
{{ paper_summary.experimental_setup }}

# Repository Code Structure
{{ repository_code_structure }}

Select the most important files (typically 5-8 files depending on repository size).
"""
