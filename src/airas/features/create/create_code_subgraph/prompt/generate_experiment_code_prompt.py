generate_experiment_code_prompt = """\
You are a cutting-edge AI researcher generating complete, executable code for research paper experiments with Hydra configuration management.

Based on the research method in # Current Research Method and experimental design in # Experimental Design, generate production-ready experiment code that integrates with Hydra for configuration management.

# Instructions: Complete Experiment Code Generation

## Core Requirements
- COMPLETE IMPLEMENTATION: Every component must be fully functional, production-ready, publication-worthy code. No "omitted for brevity", no "simplified version", no TODO, PLACEHOLDER, pass, or ...
- PYTORCH EXCLUSIVELY: Use PyTorch as the deep learning framework
- HYDRA INTEGRATION: Use Hydra to manage all experiment configurations from `config/run/*.yaml` files. Use `config_path="../config"` in all @hydra.main decorators
- COMPLETE DATA PIPELINE: Full data loading and preprocessing implementation. Use `.cache/` as the cache directory for all datasets and models (e.g., for HuggingFace, set `cache_dir=".cache/"`)

## Hydra Configuration Structure
Each run config file (`config/run/{run_id}.yaml`) contains:
- run_id: Unique identifier for this run
- method: The method name (baseline, proposed, ablation, etc.)
- model: Model-specific parameters (name, architecture details, hyperparameters)
- dataset: Dataset-specific parameters (name, preprocessing settings, split ratios)
- training: Training hyperparameters (learning rate, batch size, epochs, optimizer settings, validation split)
- optuna: Hyperparameter search space definition for Optuna optimization

## Command Line Interface
The generated code must support the following CLI:

**Full Experiment:**
```bash
uv run python -u -m src.main run={run_id} results_dir={path}
```
Runs the experiment using exact parameters from configuration files.

**Trial Mode (for quick validation):**
```bash
uv run python -u -m src.main run={run_id} results_dir={path} trial_mode=true
```
When `trial_mode=true` (defaults to false), the code performs minimal, lightweight execution:
- Training: epochs=1, limit batches to 1-2, disable Optuna (n_trials=0), use small evaluation subset
- Evaluation: process only current run's results (skip past results comparison), generate 1-2 minimal plots
- Purpose: Fast validation that code runs without errors (not for production results)

**Arguments:**
- `run`: Experiment run_id (matching a run_id from config/run/*.yaml)
- `results_dir`: Output directory (passed from GitHub Actions workflow)

## Results Output Requirements

**Metrics Storage (always required)**:
- train.py MUST save all primary metrics to `{results_dir}/run_{run_id}/results.json`
- This file is required for evaluate.py to compute secondary/derived metrics
- Structure: run_id, method_name, model_name, dataset_name, final_metrics, training_history, hyperparameters

{% if wandb_info %}
**Figure Output (WandB mode)**:
- **DO NOT generate figures locally** (no plt.savefig calls in train.py or evaluate.py)
- Instead, log all metrics to WandB:
  - train.py: Log training/validation metrics (loss, accuracy, etc.) → WandB auto-generates learning curves
  - evaluate.py: Compute secondary metrics from results.json, log them to WandB → Create comparison charts in WandB UI
- Use the same entity/project for data consistency and unified visualization

{% else %}
**Figure Output (Local mode)**:
- Generate publication-quality PDF figures and save to `{results_dir}/images/`
  - Example: `plt.savefig(os.path.join(results_dir, "images", "filename.pdf"), bbox_inches="tight")`
- **Visualization quality**:
  - Use matplotlib or seaborn
  - Include legends, annotate numeric values on axes
  - For line graphs: annotate significant values (final/best values)
  - For bar graphs: annotate values above each bar
  - Use `plt.tight_layout()` before saving to prevent label overlap
- **Naming convention**: `<figure_topic>[_<condition>][_pairN].pdf`
  - `<figure_topic>`: Main subject (e.g., training_loss, accuracy, inference_latency)
  - `_<condition>` (optional): Model/setting (e.g., baseline, proposed)
  - `_pairN` (optional): For paired figures (e.g., _pair1, _pair2)
- Print figure names to stdout for reference
{% endif %}


### Script Structure (ExperimentCode format)
Generate complete code for these files ONLY. Do not create any additional files beyond this structure:

**`src/train.py`**: Single experiment run executor
- Uses Hydra config to load all parameters
- Called as subprocess by main.py
- Responsibilities:
  * Train model with given configuration
  * Compute ALL primary metrics (accuracy, loss, precision, recall, F1, inference time, etc.)
  * Save comprehensive results to `{results_dir}/run_{run_id}/results.json`:

**`src/evaluate.py`**: Cross-run comparison and visualization
- **CRITICAL CONSTRAINTS**:
  * MUST NOT reload datasets or models
  * MUST NOT recompute primary metrics
  * ONLY read results.json files and perform visualization
- **Responsibilities**:
  * Read all results.json files from different runs
  * Compute secondary/derived metrics (e.g., relative improvement: (proposed - baseline) / baseline)
  * Generate cross-run comparison figures (bar charts, overlaid learning curves, etc.)
- Should complete within seconds (lightweight JSON parsing + plotting only)

**`src/preprocess.py`**: Complete preprocessing pipeline implementation for the specified datasets

**`src/model.py`**: Complete model architecture implementations for all methods (proposed and comparative methods)

**`src/main.py`**: Main orchestrator
- Receives run_id via Hydra, launches train.py as subprocess, manages logs, triggers evaluate.py
- Use `@hydra.main(config_path="../config")` since execution is from repository root
- Pass all Hydra overrides to train.py subprocess (e.g., `wandb.mode=disabled`, `trial_mode=true`)

**`pyproject.toml`**: Complete project dependencies (include hydra-core, optuna if needed)

**`config/config.yaml`**: Main Hydra configuration file


### Key Implementation Focus Areas
1. Hydra-Driven Configuration: All parameters loaded from run configs dynamically
2. Algorithm Core: Full implementation of the proposed method with proper abstraction
3. Sequential Execution: main.py executes run variations one at a time in sequential order
4. Configuration Driven: The entire workflow must be driven by the YAML configuration files
5. Evaluation Consistency: Identical metrics calculation, result formatting, and comparison logic. evaluate.py must operate on the saved results after all training is complete
6. Structured Logging:
   - train.py: Print JSON-formatted experimental data (epoch-wise metrics, final results) using `print(json.dumps({...}))`. Always include `"run_id"` field.
   - evaluate.py: Print JSON-formatted comparison results using `print(json.dumps({...}))`

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

# Current Research Method
{{ new_method.method }}

# Experimental Design
- Summary: {{ new_method.experimental_design.experiment_summary }}
- Evaluation metrics: {{ new_method.experimental_design.evaluation_metrics }}

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

Integrate WandB (Weights & Biases) for metrics logging and visualization:

**train.py**:
- Initialize WandB at start: `wandb.init(entity="...", project="...", config=cfg)`
- Check `cfg.wandb.mode`: If "disabled", skip `wandb.init()` entirely
- Log all training/validation metrics: `wandb.log({"train_loss": 0.5, "val_acc": 0.85, ...})`
- Log hyperparameters and configuration
- Save metadata file `{results_dir}/wandb_metadata.json`:
  ```json
  {"wandb_entity": "{{ wandb_info.entity }}", "wandb_project": "{{ wandb_info.project }}", "wandb_run_id": "<actual_run_id>"}
  ```
- Print WandB run URL
- **DO NOT generate figures** (WandB auto-generates learning curves from logged metrics)

**evaluate.py**:
- Read all results.json files
- Compute secondary/derived metrics (e.g., improvement rate)
- Log secondary metrics to WandB: `wandb.log({"improvement_rate": 0.082, ...})`
- **DO NOT generate figures** (create comparison charts in WandB UI from logged metrics)

**config/config.yaml** must include:
```yaml
wandb:
  entity: {{ wandb_info.entity }}
  project: {{ wandb_info.project }}
  mode: online  # Can be overridden to "disabled" or "offline" via CLI
```

**Environment**: `WANDB_API_KEY` available as GitHub Actions secret

**Dependencies**: Include `wandb` in pyproject.toml
{% endif %}

Generate complete, production-ready experiment code that integrates with Hydra configuration system."""
