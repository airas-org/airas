generate_experiment_code_prompt = """\
You are a cutting-edge AI researcher. Based on the new method described in # New Methods, the experimental policy outlined in # Experiment Strategy, and the detailed experimental specifications provided in # Experiment Specification, please present detailed code for conducting the experiments according to the instructions below.

# Instructions

## Basic Requirements
- The generated code will be executed as `python -m src.main` without any command-line arguments.
- Output Python code to conduct each experiment based on the detailed information provided in "Experiment Specification".
- At the beginning, output the names of the Python libraries that you believe are necessary to run the experiments.
- Use PyTorch exclusively as the deep learning framework.
- Make full use of existing Python libraries where possible and avoid implementing from scratch.

## Implementation Guidelines
- Complete data pipeline: Implement full data acquisition from URLs, including downloading, extraction, and organizing into data/ directory. Do not assume existing local data.
- Comprehensive experiments: Implement full-scale experiments, not quick tests or prototypes. Include sufficient training epochs, proper validation splits, and thorough evaluation metrics.
- Fail-fast, no silent fallbacks: Add assert statements or exceptions for critical operations, remove default values or mock data that hide real issues.

## Output Requirements
The implementation must ensure that all experiment executions include the following in the standard output:

### Standard Output Content
- **Experiment description**: Before printing experimental results, the standard output must include a detailed description of the experiment.
- **Experimental numerical data**: All experimental data obtained in the experiments must be output to the standard output.
- **Names of figures summarizing the numerical data**

### Figure Output Requirements
- Experimental results must be presented in clear and interpretable figures.
- Use matplotlib or seaborn to output the results (e.g., accuracy, loss curves, confusion matrix).
- Numeric values must be annotated on the axes of the graphs.
- For line graphs, annotate values on the plot; for bar graphs, annotate values above each bar.
- Include legends in the figures.
- All figures must be saved in .pdf format (e.g., using plt.savefig("filename.pdf", bbox_inches="tight")).
  - Do not use .png or any other formats—only .pdf is acceptable for publication quality.

### Figure Naming Convention
File names must follow the format: `<figure_topic>[_<condition>][_pairN].pdf`
- `<figure_topic>`: The main subject of the figure (e.g., training_loss, accuracy, inference_latency)
- `_<condition>` (optional): Indicates model, setting, or comparison condition (e.g., amict, baseline, tokens, multimodal_vs_text)
- `_pairN` (optional): Used when presenting figures in pairs (e.g., _pair1, _pair2)
- For standalone figures, do not include _pairN.

{% if consistency_feedback %}
## Consistency Feedback
**Important**: Address the following feedback from previous experimental consistency evaluation:
{{ consistency_feedback }}

Specifically improve the experimental code to resolve these consistency issues.
{% endif %}

{% if previous_method and previous_method.experimental_design %}
# Previous Iteration Reference

## Previous Experimental Design
- **Strategy**: {{ previous_method.experimental_design.experiment_strategy }}
- **Details**: {{ previous_method.experimental_design.experiment_details }}
- **Code Approach**: {{ previous_method.experimental_design.experiment_code }}

{% if previous_method.experimental_results %}
## Previous Results
- **Result**: {{ previous_method.experimental_results.result }}
{% endif %}

Build upon what worked and address what didn't work to improve the consistency score.
{% endif %}

# Experimental Environment
{{ runtime_prompt }}

{% if new_method.experimental_design.external_resources %}
# External Resources
{{ new_method.experimental_design.external_resources }}
{% endif %}

# New Methods
{{ new_method.method }}

# Experiment Strategy
{{ new_method.experimental_design.experiment_strategy }}

# Experiment Specification
{{ new_method.experimental_design.experiment_details }}"""
