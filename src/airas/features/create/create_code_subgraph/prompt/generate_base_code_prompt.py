generate_base_code_prompt = """\
You are a cutting-edge AI researcher preparing the COMMON CORE FOUNDATION for experiments that will ensure consistency across all experimental variations.

This step generates the **COMMON CORE FOUNDATION** for experiments that will ensure consistency across all experimental variations.

**Current Task**: Generate common base logic, evaluation framework, and infrastructure with placeholders for specific datasets/models
**Next Step**: A subsequent step will derive specific experiments by replacing placeholders with actual datasets/models

Based on the research method in # Current Research Method and experimental design in # Experimental Design, generate the foundational code that will serve as the common base for ALL experimental variations.

# Instructions: Common Core Foundation Generation

## Core Requirements
- **COMMON EVALUATION LOGIC**: Implement consistent evaluation metrics, result collection, and comparison logic that will work across all experimental variations
- **CORE ALGORITHM IMPLEMENTATION**: Implement the main method/algorithm with full functionality
- **INFRASTRUCTURE CODE**: Complete training loops, model saving/loading, configuration handling, and result visualization
- **PLACEHOLDER STRATEGY**: Use clear, descriptive placeholders for dataset-specific and model-specific components that will be replaced in subsequent steps
- **CONSISTENCY FRAMEWORK**: Ensure all experiments will use identical evaluation criteria, metrics calculation, and result formatting

## Placeholder Guidelines
- Use descriptive placeholder names like `DATASET_PLACEHOLDER`, `MODEL_PLACEHOLDER`, `SPECIFIC_CONFIG_PLACEHOLDER`
- Include comments explaining what will be replaced: `# PLACEHOLDER: Will be replaced with specific dataset loading logic`
- Ensure placeholders are easily identifiable and replaceable in the next phase
- Keep the base logic intact - only dataset/model-specific parts should be placeholders

## Implementation Requirements
- **ZERO PLACEHOLDER POLICY FOR CORE LOGIC**: Generate complete, production-ready base framework. NO placeholders for training loops, evaluation logic, or result processing.
- **COMPLETE IMPLEMENTATION**: Every base component must be fully functional. No "omitted for brevity", no "simplified version" for base logic.
- **PUBLICATION-READY INFRASTRUCTURE**: Framework must produce actual publication-worthy results when datasets/models are specified
- **USE PYTORCH EXCLUSIVELY** as the deep learning framework
- **COMPLETE DATA PIPELINE FRAMEWORK**: Implement data loading and preprocessing pipeline with placeholders for specific datasets
- **COMPREHENSIVE EXPERIMENT INFRASTRUCTURE**: Full-scale experiment framework with sufficient training epochs, proper validation splits, and thorough evaluation metrics
- **STRUCTURED PLACEHOLDER APPROACH**: Use well-defined placeholders for dataset/model specifics while ensuring base logic is complete and functional

## Standard Output Content Requirements
- Experiment description: Before printing experimental results, the standard output must include a detailed description of the experiment.
- Experimental numerical data: All experimental data obtained in the experiments must be output to the standard output.
- Names of figures summarizing the numerical data

## Figure Output Requirements
- Experimental results must always be presented in clear and interpretable figures without exception.
- Use matplotlib or seaborn to output the results (e.g., accuracy, loss curves, confusion matrix).
- Numeric values must be annotated on the axes of the graphs.
- For line graphs, annotate significant values (e.g., the final or best value) to highlight key findings. For bar graphs, annotate the value above each bar.
- Include legends in the figures.
- All figures must be saved in .pdf format (e.g., using plt.savefig("filename.pdf", bbox_inches="tight")).
  - Do not use .png or any other formats—only .pdf is acceptable for publication quality.

## Figure Naming Convention
File names must follow the format: `<figure_topic>[_<condition>][_pairN].pdf`
- `<figure_topic>`: The main subject of the figure (e.g., training_loss, accuracy, inference_latency)
- `_<condition>` (optional): Indicates model, setting, or comparison condition (e.g., amict, baseline, tokens, multimodal_vs_text)
- `_pairN` (optional): Used when presenting figures in pairs (e.g., _pair1, _pair2)
- For standalone figures, do not include _pairN.

{% if secret_names %}
- Environment Variables: The following environment variables are available: {{ secret_names|join(', ') }}
{% endif %}

## Command Line Interface and Run Variations
The `full_experiment.yaml` file defines a list of all experiments to be run (e.g., baseline, proposed, ablations). The `main.py` script reads this file and executes experiments sequentially.

The generated main.py must support:
```bash
# Smoke test (runs a lightweight version of ALL run variations defined in smoke_test.yaml)
uv run python -m src.main --smoke-test --results-dir <path>

# Full experiment (reads full_experiment.yaml, runs all variations sequentially)
uv run python -m src.main --full-experiment --results-dir <path>
```

The `--results-dir` argument is passed from the GitHub Actions workflow and specifies where all outputs (figures, logs, metrics) should be saved.

## Output Structure
Generate complete foundational code for these files ONLY. Do not create any additional files beyond this structure:

### Script Structure (ExperimentCode format)
Generate complete foundational code for these files ONLY. Do not create any additional files beyond this structure:
- `src/train.py`: Logic to run a single experiment variation. It is called as a subprocess by main.py. It must save final metrics to a structured file (e.g., results.json).
- `src/evaluate.py`: Comparison and visualization tool. It reads the result files from all experiment variations and generates comparison figures.
- `src/preprocess.py`: Common preprocessing pipeline with dataset placeholders
- `src/model.py`: Model architecture implementations. It will contain classes for baseline, proposed, and ablation models.
- `src/main.py`: The main orchestrator script. It reads a config file, launches train.py for each experiment sequentially, manages subprocesses, collects and consolidates logs, and finally triggers evaluate.py.
- `pyproject.toml`: Complete project dependencies
- `config/smoke_test.yaml`: Configuration file template with placeholder structure for run variations. Actual variations will be populated in derive_specific step.
- `config/full_experiment.yaml`: Configuration file template with placeholder structure for run variations. Actual variations will be populated in derive_specific step.

### Key Implementation Focus Areas
1. Algorithm Core: Full implementation of the proposed method with proper abstraction
2. Sequential Execution: main.py executes run variations one at a time in sequential order.
3. Configuration Driven: The entire workflow must be driven by the YAML configuration files.
4. Evaluation Consistency: Identical metrics calculation, result formatting, and comparison logic. evaluate.py must operate on the saved results after all training is complete.
5. Structured Logging:
   - train.py: Print JSON-formatted experimental data (epoch-wise metrics, final results) to stdout using `print(json.dumps({...}))`. Always include `"run_id"` field (use the run variation name from config).
   - evaluate.py: Print JSON-formatted comparison results to stdout
   - main.py: For each subprocess, redirect stdout/stderr to `{results_dir}/{run_id}/stdout.log` and `{results_dir}/{run_id}/stderr.log` while also forwarding to main process stdout/stderr (using tee-like logic) so logs are captured both structurally and by GitHub Actions.

{% if base_code_validation %}
## Core code Validation Feedback
{% set is_ready, issue = base_code_validation %}
{% if not is_ready and issue %}
**Previous Validation Issue**: {{ issue }}
**Action Required**: Address this by ensuring the base framework provides a solid foundation for experimental implementations.
{% endif %}
{% endif %}

# Experimental Environment
{{ runner_type_prompt }}

# Current Research Method (Target for Experiment Design)
{{ new_method.method }}

# Experimental Design
- Strategy: {{ new_method.experimental_design.experiment_strategy }}

{% if consistency_feedback %}
## Consistency Feedback
**Critical**: Address the following consistency requirements in your base framework:
{{ consistency_feedback }}

Ensure your foundational code addresses these consistency issues across all future experimental variations.
{% endif %}

# Reference Information from Previous Iteration
{% if new_method.iteration_history %}
## Previous Experimental Design
- Strategy: {{ new_method.iteration_history[-1].experimental_design.experiment_strategy }}
- Details: {{ new_method.iteration_history[-1].experimental_design.experiment_details }}
{% endif %}

Remember: This is the FOUNDATION that will ensure ALL experimental variations are conducted on the same rigorous, consistent basis. Focus on creating robust base logic with strategic placeholders for dataset/model specifics."""
