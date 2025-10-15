generate_experiment_code_prompt = """\
You are a cutting-edge AI researcher generating complete, executable code for research paper experiments with Hydra configuration management.

Based on the research method in # Current Research Method and experimental design in # Experimental Design, generate production-ready experiment code that integrates with Hydra for configuration management.

# Instructions: Complete Experiment Code Generation

## Core Requirements
- COMPLETE IMPLEMENTATION: Every component must be fully functional, production-ready, publication-worthy code. No "omitted for brevity", no "simplified version", no TODO, PLACEHOLDER, pass, or ...
- PYTORCH EXCLUSIVELY: Use PyTorch as the deep learning framework
- HYDRA INTEGRATION: Use Hydra to manage all experiment configurations from `config/run/*.yaml` files
- COMPLETE DATA PIPELINE: Full data loading and preprocessing implementation

## Hydra Configuration Structure
Each run config file (`config/run/{run_id}.yaml`) contains:
- run_id: Unique identifier for this run
- method: The method name (baseline, proposed, ablation, etc.)
- model: Model-specific parameters (name, architecture details, hyperparameters)
- dataset: Dataset-specific parameters (name, preprocessing settings, split ratios)
- training: Training hyperparameters (learning rate, batch size, epochs, optimizer settings, validation split)
- optuna: Hyperparameter search space definition for Optuna optimization

## Standard Output Content Requirements
- Experiment description: Before printing experimental results, the standard output must include a detailed description of the experiment.
- Experimental numerical data: All experimental data obtained in the experiments must be output to the standard output.

## Command Line Interface
The generated code must support the following CLI:
- Full Experiment: Runs the experiment using the exact parameters from the configuration files.
```bash
uv run python -u -m src.main run={run_id} results_dir={path}
```
- Trial Mode: For quick validation, a trial_mode=true flag must be supported. When enabled, the code should override configurations for a minimal run (e.g., set training.epochs=1 and disable Optuna by setting optuna.n_trials=0). This flag defaults to false.
```bash
uv run python -u -m src.main run={run_id} results_dir={path} trial_mode=true
```

The `run` argument specifies which experiment to run (matching a run_id from config/run/*.yaml).
The `results_dir` argument is passed from the GitHub Actions workflow and specifies where all outputs should be saved.

## Output Structure
Generate complete code for these files ONLY. Do not create any additional files beyond this structure:

### Script Structure (ExperimentCode format)
- `src/train.py`: Logic to run a single experiment variation. Uses Hydra config to load parameters. It is called as a subprocess by main.py. It must save final metrics to a structured file (e.g., results.json).
- `src/evaluate.py`: Comparison and visualization tool. It reads the result files from all experiment variations and generates comparison figures.
- `src/preprocess.py`: Complete preprocessing pipeline implementation for the specified datasets
- `src/model.py`: Complete model architecture implementations. It will contain classes for baseline, proposed, and ablation models. Implement all architectures from scratch.
- `src/main.py`: The main orchestrator script. It receives a run_id via Hydra, launches train.py for that specific experiment, manages subprocess, collects and consolidates logs, and finally triggers evaluate.py if needed.
- `pyproject.toml`: Complete project dependencies (include hydra-core, optuna if needed)
- `config/config.yaml`: Main Hydra configuration file that defines the list of all experiment run_ids


### Key Implementation Focus Areas
1. Hydra-Driven Configuration: All parameters loaded from run configs dynamically
2. Algorithm Core: Full implementation of the proposed method with proper abstraction
3. Sequential Execution: main.py executes run variations one at a time in sequential order
4. Configuration Driven: The entire workflow must be driven by the YAML configuration files
5. Evaluation Consistency: Identical metrics calculation, result formatting, and comparison logic. evaluate.py must operate on the saved results after all training is complete
6. Structured Logging:
   - train.py: Print JSON-formatted experimental data (epoch-wise metrics, final results) to stdout using `print(json.dumps({...}))`. Always include `"run_id"` field (use the run variation name from config).
   - evaluate.py: Print JSON-formatted comparison results to stdout
   - main.py: For each subprocess, redirect stdout/stderr to `{results_dir}/{run_id}/stdout.log` and `{results_dir}/{run_id}/stderr.log` while also forwarding to main process stdout/stderr (using tee-like logic) so logs are captured both structurally and by GitHub Actions.

{% if code_validation %}
## Code Validation Feedback
{% set is_ready, issue = code_validation %}
{% if not is_ready and issue %}
**Previous Validation Issue**: {{ issue }}
**Action Required**: Address this issue in the implementation.
{% endif %}
{% endif %}

# Experimental Environment
{{ runner_type_prompt }}

# Current Research Method (Target for Experiment Design)
{{ new_method.method }}

# Experimental Design
- Strategy: {{ new_method.experimental_design.experiment_strategy }}

# Experiment Runs
{% for run in new_method.experiment_runs %}
- Run ID: {{ run.run_id }}
  Method: {{ run.method_name }}
  Model: {{ run.model_name }}
  Dataset: {{ run.dataset_name }}
  Config File: config/run/{{ run.run_id }}.yaml
  {% if run.run_config %}
  Config Content:
  ```yaml
  {{ run.run_config }}
  ```
  {% endif %}
{% endfor %}

# External Resources (Use these for implementation)
{% if new_method.experimental_design.external_resources and new_method.experimental_design.external_resources.hugging_face %}
**HuggingFace Models:**
{% for model in new_method.experimental_design.external_resources.hugging_face.models %}
- ID: {{ model.id }}
{% if model.extracted_code %}
- Code: {{ model.extracted_code }}
{% endif %}
{% endfor %}

**HuggingFace Datasets:**
{% for dataset in new_method.experimental_design.external_resources.hugging_face.datasets %}
- ID: {{ dataset.id }}
{% if dataset.extracted_code %}
- Code: {{ dataset.extracted_code }}
{% endif %}
{% endfor %}
{% endif %}

{% if wandb_info %}
# ========================================
# WandB Integration Requirements
# ========================================

## Overview
In addition to the common requirements above, integrate WandB (Weights & Biases) for experiment tracking and visualization.

## Additional Requirements
- WANDB INTEGRATION: Initialize WandB with proper project/entity from config, log metrics/artifacts, and save wandb_run_id to metadata
- WANDB METADATA: Save WandB run information to `.research/iteration{experiment_iteration}/wandb_metadata.json` with structure:
  ```json
  {
    "wandb_entity": "{{ wandb_info.entity }}",
    "wandb_project": "{{ wandb_info.project }}",
    "wandb_run_id": "<actual_run_id_from_wandb>"
  }
  ```
- Initialization: Initialize WandB at the start of each training run with config from Hydra
- Metric Logging: Log all training/validation metrics to WandB (loss, accuracy, etc.)
- Artifact Tracking: Log model checkpoints and important artifacts
- Metadata Saving: After WandB initialization, save the wandb_run_id to `.research/iteration{experiment_iteration}/wandb_metadata.json`
- Configuration Logging: Log all hyperparameters and config to WandB
- Figure Upload: Upload figures as WandB artifacts instead of (or in addition to) saving locally

## WandB Configuration
- Entity: {{ wandb_info.entity }}
- Project: {{ wandb_info.project }}

## Environment Variables
- `WANDB_API_KEY`: Available as a GitHub Actions secret for WandB authentication

## Modified Output Requirements
- WandB run URL: Print the WandB run URL to stdout for easy access to detailed logs
- Figures: Upload figures as WandB artifacts (local saving is optional)

## Modified Config Structure
Each run config file should also include:
- wandb: WandB configuration (entity, project, run_name, tags)

## Modified Dependencies
- pyproject.toml: Include `wandb` package

## WandB Metadata File Location
The wandb_metadata.json file must be saved to:
- Path: `.research/iteration{experiment_iteration}/wandb_metadata.json`
- The experiment_iteration should be passed as an environment variable or config parameter
- The file should be created immediately after WandB run initialization in train.py

{% else %}
# ========================================
# Figure Output Requirements (Non-WandB)
# ========================================

- Experimental results must always be presented in clear and interpretable figures without exception.
- Use matplotlib or seaborn to output the results (e.g., accuracy, loss curves, confusion matrix).
- Numeric values must be annotated on the axes of the graphs.
- For line graphs, annotate significant values (e.g., the final or best value) to highlight key findings. For bar graphs, annotate the value above each bar.
- Include legends in the figures.
- To prevent labels, titles, and legends from overlapping, use `plt.tight_layout()` before saving the figure.
- All figures must be saved to `{results_dir}/images/` directory in .pdf format (e.g., using `plt.savefig(os.path.join(results_dir, "images", "filename.pdf"), bbox_inches="tight")`).
  - Do not use .png or any other formats—only .pdf is acceptable for publication quality.
- Names of figures summarizing the numerical data should be printed to stdout

## Figure Naming Convention
File names must follow the format: `<figure_topic>[_<condition>][_pairN].pdf`
- `<figure_topic>`: The main subject of the figure (e.g., training_loss, accuracy, inference_latency)
- `_<condition>` (optional): Indicates model, setting, or comparison condition (e.g., amict, baseline, tokens, multimodal_vs_text)
- `_pairN` (optional): Used when presenting figures in pairs (e.g., _pair1, _pair2)
- For standalone figures, do not include _pairN.
{% endif %}

Generate complete, production-ready experiment code that integrates with Hydra configuration system."""
