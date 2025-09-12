generate_experiment_code_prompt = """\
You are a cutting-edge AI researcher preparing experiments for a research paper publication.
Based on the new method described in # Current Research Method, the experimental policy outlined in # Experiment Strategy and the detailed experimental specifications provided in # Experiment Details,
please present detailed code for conducting rigorous experiments that will generate publication-worthy results according to the instructions below.

# Instructions

## Basic Requirements
- Research Publication Quality: Implement comprehensive, rigorous experiments that produce meaningful, publication-worthy results - NOT placeholder or toy experiments.
- Output Python code to conduct each experiment based on the detailed information provided in "Experiment Details".
- Include dataset URLs, model specifications, and hyperparameters as structured configuration that can be extracted into YAML.
- Generate two YAML configuration files: one for smoke testing (quick validation with minimal resources) and one for full experiments (complete evaluation with full datasets).
- Use PyTorch exclusively as the deep learning framework.
- Make full use of existing Python libraries where possible and avoid implementing from scratch.

## Implementation Guidelines
- Complete data pipeline: Implement full data acquisition from URLs, including downloading, extraction, and organizing into data/ directory. Do not assume existing local data.
- Comprehensive experiments: Implement full-scale experiments, not quick tests or prototypes. Include sufficient training epochs, proper validation splits, and thorough evaluation metrics.
- STRICT NO-FALLBACK RULE: If real datasets or models cannot be accessed, terminate execution immediately with clear error messages - NEVER use synthetic/dummy/placeholder data under any circumstances.
{% if secret_names %}
- Environment Variables: The following environment variables are available for use in your experiments: {{ secret_names|join(', ') }}. These can be accessed using os.getenv() in your Python code.
{% endif %}

## Command Line Execution Requirements
The generated main.py must support the following command patterns:
```bash
# Smoke test only
uv run python -m src.main --smoke-test

# Full experiment only
uv run python -m src.main --full-experiment
```

## Output Requirements
When implementing the code, ensure that the output strictly adheres to the following rules.:

### Results Documentation
- Save the results of each experiment as separate JSON files and modify the code to print the contents of the JSON files to standard output using a print statement.

### Standard Output Content
- Experiment description: Before printing experimental results, the standard output must include a detailed description of the experiment.
- Experimental numerical data: All experimental data obtained in the experiments must be output to the standard output.
- Names of figures summarizing the numerical data

### Figure Output Requirements
- Experimental results must always be presented in clear and interpretable figures without exception.
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

# Experimental Environment
{{ runner_type_prompt }}

{% if new_method.experimental_design.external_resources %}
# External Resources
{{ new_method.experimental_design.external_resources }}
{% endif %}

# Current Research Method (Target for Experiment Design)
{{ new_method.method }}

# Experiment Strategy
{{ new_method.experimental_design.experiment_strategy }}

# Experiment Details
{{ new_method.experimental_design.experiment_details }}

---
# Reference Information from Previous Iteration
{% if new_method.iteration_history %}
## Previous Experimental Design
- **Strategy**: {{ new_method.iteration_history[-1].experimental_design.experiment_strategy }}
- **Details**: {{ new_method.iteration_history[-1].experimental_design.experiment_details }}

{% if generated_file_contents %}
## Previous Generated Code Files
{% for filename, content in generated_file_contents.items() %}
### {{ filename }}
```python
{{ content }}
```
{% endfor %}
{% endif %}

Build upon what worked and address what didn't work to improve the consistency score.
{% else %}
*No previous iteration available*
{% endif %}
---"""
