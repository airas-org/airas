generate_experiment_code_prompt = """\
You are a creative AI researcher. Based on the new method described in # New Methods, the experimental policy outlined in # Experiment Strategy, and the detailed experimental specifications provided in # Experiment Specification, please follow the instructions below and provide the detailed code for conducting the experiments.

# Instructions
- Output detailed experiment code for each experiment.
- Since the experiment results will be checked via standard output, use print statements to ensure the experimental content and results can be clearly understood from the output.
- Add a test function to verify that the code runs correctly. The test should complete quickly, as it is only intended to check functionality.
- Use PyTorch exclusively for all deep learning frameworks.
- Prepare multiple patterns of data during the experiments and design the code to demonstrate the robustness of the new method.
- Also output the names of the Python libraries that you believe are necessary to run the experiments.
<<<<<<< HEAD
- Please use matplotlib or seaborn to plot the results (e.g., accuracy, loss curves, confusion matrix),and **explicitly save all plots as `.pdf` files using `plt.savefig("filename.pdf", bbox_inches="tight")` or equivalent.
=======
- Please use matplotlib or seaborn to plot the results (e.g., accuracy, loss curves, confusion matrix),
and **explicitly save all plots as `.pdf` files using `plt.savefig("filename.pdf", bbox_inches="tight")` or equivalent.
>>>>>>> develop
    - Do not use `.png` or other formats—output must be `.pdf` only. These plots should be suitable for inclusion in academic papers.
- Use the following filename format:
    <figure_topic>[_<condition>][_pairN].pdf
    - `<figure_topic>`: the main subject of the figure (e.g., `training_loss`, `accuracy`, `inference_latency`)
    - `_<condition>`(optional): a specific model, setting, or comparison (e.g., `amict`, `baseline`, `tokens`, `multimodal_vs_text`)
    - `_pairN`(optional): indicates that the figure is part of a pair (e.g., `_pair1`, `_pair2`) to be shown side by side using subfigures
    - If the figure is not part of a pair (i.e., there is only one figure), **do not include `_pairN` in the filename**.

{% if consistency_feedback %}
- **Important**: Address the following feedback from previous experimental consistency evaluation:
{{ consistency_feedback }}
- Specifically improve the experimental code to resolve these consistency issues.
{% endif %}

# New Methods
{{ new_method }}
# Experiment Strategy
{{ experiment_strategy }}
# Experiment Details
{{ experiment_details }}"""
