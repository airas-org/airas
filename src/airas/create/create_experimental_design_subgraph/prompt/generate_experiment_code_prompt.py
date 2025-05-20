generate_experiment_code_prompt = """\
# Introduction
Please follow the instructions below to tell us the detailed code for conducting the experiment.
- Please output the detailed experiment code for each experiment.
- As you will be checking the results of the experiment from the standard output, please include print statements, etc. in your implementation so that the contents of the experiment and its results, etc. can be accurately understood from the standard output.
- Please add a function to test the code to check that it is executed correctly. As the test is to check that the code is working correctly, please make it so that the test finishes immediately.
- Please implement all frameworks used for deep learning in pytorch.
- When conducting experiments, please prepare multiple patterns of data and create an experimental code that demonstrates the robustness of the new method.
- Please also output the names of the python libraries that you think are necessary for running the experiment.
- The section 'Experimental code from the research on which it is based' and 'Experimental information from the research on which it is based' includes details about the experiments conducted in the original research. Please use this information to implement the experiment as closely as possible to the original.
- Please use matplotlib or seaborn to plot the results (e.g., accuracy, loss curves, confusion matrix), 
and **explicitly save all plots as `.pdf` files using `plt.savefig("filename.pdf", bbox_inches="tight")` or equivalent.
    - Do not use `.png` or other formats—output must be `.pdf` only. These plots should be suitable for inclusion in academic papers.
- Use the following filename format:
    <figure_topic>[_<condition>][_pairN].pdf
    - `<figure_topic>`: the main subject of the figure (e.g., `training_loss`, `accuracy`, `inference_latency`)
    - `_<condition>`(optional): a specific model, setting, or comparison (e.g., `amict`, `baseline`, `tokens`, `multimodal_vs_text`)
    - `_pairN`(optional): indicates that the figure is part of a pair (e.g., `_pair1`, `_pair2`) to be shown side by side using subfigures
    - If the figure is not part of a pair (i.e., there is only one figure), **do not include `_pairN` in the filename**.

# Experiment Details
-------------------------
{{ experiment_details }}
-------------------------
# Experimental code from the research on which it is based
---------------------------
{{ base_experimental_code }}
---------------------------
# Experimental information from the research on which it is based
---------------------------
{{ base_experimental_info }}"""
