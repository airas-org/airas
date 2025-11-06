generate_experiment_code_prompt = """\
You are a cutting-edge AI researcher generating complete, executable code for research paper experiments with Hydra configuration management.

Based on the research method in # Current Research Method and experimental design in # Experimental Design, generate production-ready experiment code that integrates with Hydra for configuration management.

# Instructions: Complete Experiment Code Generation

## Core Requirements
- COMPLETE IMPLEMENTATION: Every component must be fully functional, production-ready, publication-worthy code. No "omitted for brevity", no "simplified version", no TODO, PLACEHOLDER, pass, or ...
- PYTORCH EXCLUSIVELY: Use PyTorch as the deep learning framework
- HYDRA INTEGRATION: Use Hydra to manage all experiment configurations from `config/runs/*.yaml` files. Use `config_path="../config"` in all @hydra.main decorators
- COMPLETE DATA PIPELINE: Full data loading and preprocessing implementation. Use `.cache/` as the cache directory for all datasets and models (e.g., for HuggingFace, set `cache_dir=".cache/"`)
- WANDB REQUIRED: WandB is mandatory for metrics logging (except trial_mode validation)

## Hydra Configuration Structure
Each run config file (`config/runs/{run_id}.yaml`) contains:
- run_id: Unique identifier for this run
- method: The method name (baseline, proposed, ablation, etc.)
- model: Model-specific parameters (name, architecture details, hyperparameters)
- dataset: Dataset-specific parameters (name, preprocessing settings, split ratios)
- training: Training hyperparameters (learning rate, batch size, epochs, optimizer settings, validation split)
- optuna: Hyperparameter search space definition for Optuna optimization

## Command Line Interface
The generated code must support the following CLI:

**Training (main.py):**
```bash
# Full experiment with WandB logging
uv run python -u -m src.main run={run_id} results_dir={path} mode=full

# Trial mode (validation only, WandB disabled)
uv run python -u -m src.main run={run_id} results_dir={path} mode=trial
```
- `run`: Experiment run_id (matching a run_id from config/runs/*.yaml)
- `results_dir`: Output directory (passed from GitHub Actions workflow)
- `mode`: Execution mode (required parameter)
  * `mode=trial`: Lightweight execution for validation (epochs=1, batches limited to 1-2, wandb.mode=disabled, optuna.n_trials=0)
  * `mode=full`: Full experiment execution (wandb.mode=online, full epochs, full Optuna trials)
  * **Code must automatically configure based on mode (e.g., `if cfg.mode == "trial": cfg.wandb.mode = "disabled"; cfg.optuna.n_trials = 0` elif `cfg.mode == "full": cfg.wandb.mode = "online"`)**

**Evaluation (evaluate.py, independent execution):**
```bash
uv run python -m src.evaluate results_dir={path} run_ids='["run-1", "run-2", ...]'
```
- `results_dir`: Directory containing experiment metadata and where outputs will be saved
- `run_ids`: JSON string list of run IDs to evaluate (e.g., '["run-1-proposed-bert-glue", "run-2-baseline-bert-glue"]')
- Executed as a separate workflow after all training runs complete
- **NOT called from main.py**

## Script Structure (ExperimentCode format)
Generate complete code for these files ONLY. Do not create any additional files beyond this structure:

**`src/train.py`**: Single experiment run executor
- Uses Hydra config to load all parameters
- Called as subprocess by main.py
- Responsibilities:
  * Train model with given configuration
  * Initialize WandB: `wandb.init(entity=cfg.wandb.entity, project=cfg.wandb.project, id=cfg.run.run_id, config=OmegaConf.to_container(cfg, resolve=True), resume="allow")`
  * Skip `wandb.init()` if `cfg.wandb.mode == "disabled"` (trial_mode)
  * **Optuna Integration**: If using Optuna for hyperparameter search, DO NOT log intermediate trial results to WandB - only train once with the best hyperparameters after optimization completes and log that final run
  * **Log ALL metrics to WandB comprehensively**:
    - Use `wandb.log()` at each training step/batch/epoch with ALL relevant metrics
    - Log as frequently as possible (per-batch or per-epoch) to capture training dynamics
    - Use CONSISTENT metric names across train.py and evaluate.py (e.g., if train.py logs "train_acc", evaluate.py MUST use run.history(keys=["train_acc",...]))
  * **Save final/best metrics to WandB summary**:
    - Use `wandb.summary["key"] = value` for final results
  * Print WandB run URL to stdout
- **NO results.json, no stdout JSON output, no figure generation**

**`src/evaluate.py`**: Independent evaluation and visualization script
- **Execution**: Run independently via `uv run python -m src.evaluate results_dir={path} run_ids='["run-1", "run-2"]'`
- **NOT called from main.py** - executes as separate workflow after all training completes
- **Responsibilities**:
  * Parse command line arguments:
    - `results_dir`: Output directory path
    - `run_ids`: JSON string list of run IDs (parse with `json.loads(args.run_ids)`)
  * Load WandB config from `config/config.yaml` (in repository root)
  * **Retrieve comprehensive experimental data from WandB API** for specified run_ids:
    ```python
    import json
    api = wandb.Api()
    run_ids = json.loads(args.run_ids)  # Parse JSON string to list
    for run_id in run_ids:
        run = api.run(f"{entity}/{project}/{run_id}")
        history = run.history()  # pandas DataFrame with ALL time-series metrics (train_loss, val_acc, etc.)
        summary = run.summary._json_dict  # Final/best metrics (best_val_acc, final_test_acc, etc.)
        config = dict(run.config)  # Run configuration (hyperparameters, model settings, etc.)
    ```
  * **STEP 1: Per-Run Processing** (for each run_id):
    - Export **comprehensive** run-specific metrics to: `{results_dir}/{run_id}/metrics.json`
    - Generate run-specific figures (learning curves, confusion matrices) to: `{results_dir}/{run_id}/`
    - Each run should have its own subdirectory with its metrics and figures
  * **STEP 2: Aggregated Analysis** (after processing all runs):
    - Export aggregated metrics to: `{results_dir}/comparison/aggregated_metrics.json`
    - Compute secondary/derived metrics (e.g., improvement rate: (proposed - baseline) / baseline)
    - Generate comparison figures to: `{results_dir}/comparison/`:
      * Cross-run comparison charts (bar charts, box plots)
      * Performance metrics tables
      * Statistical significance tests
  * **Figure Generation Guidelines**:
    - Use matplotlib or seaborn with proper legends, annotations, tight_layout
    - For line graphs: annotate significant values (final/best values)
    - For bar graphs: annotate values above each bar
    - Use GLOBALLY UNIQUE image filenames to prevent collisions across different runs and directories**:
      * Per-run figures: `{run_id}_{figure_topic}[_<condition>][_pairN].pdf` (e.g., `run-1-proposed-bert-glue_learning_curve.pdf`)
      * Comparison figures: `comparison_{figure_topic}[_<condition>][_pairN].pdf` (e.g., `comparison_accuracy_bar_chart.pdf`)
  * Print all generated file paths to stdout (both per-run and comparison)

**`src/preprocess.py`**: Complete preprocessing pipeline implementation for the specified datasets

**`src/model.py`**: Complete model architecture implementations for all methods (proposed and comparative methods)

**`src/main.py`**: Main orchestrator
- Receives run_id via Hydra, launches train.py as subprocess, manages logs
- **DOES NOT call evaluate.py** (evaluate.py runs independently in separate workflow)
- Use `@hydra.main(config_path="../config")` since execution is from repository root
- **Mode handling**: Automatically configure based on `cfg.mode`:
  * When `cfg.mode == "trial"`: Set `cfg.wandb.mode = "disabled"`, `cfg.optuna.n_trials = 0`, epochs=1, etc.
  * When `cfg.mode == "full"`: Set `cfg.wandb.mode = "online"` and use full configuration

**`config/config.yaml`**: Main Hydra configuration file
- MUST include WandB configuration:
  ```yaml
  wandb:
    entity: {{ wandb_info.entity }}
    project: {{ wandb_info.project }}
    mode: online  # Automatically set to "disabled" in trial_mode
  ```
- `WANDB_API_KEY` environment variable is automatically available for authentication

**`pyproject.toml`**: Complete project dependencies
- MUST include: `hydra-core`, `wandb` (required)
- Include as needed: `optuna`, `torch`, `transformers`, `datasets`, etc.


## Key Implementation Focus Areas
1. **Hydra-Driven Configuration**: All parameters loaded from run configs dynamically
2. **Algorithm Core**: Full implementation of the proposed method with proper abstraction
3. **Mode-Based Behavior**: Code must automatically configure based on `cfg.mode` ("trial" vs "full")
   - `mode=trial`: Set `cfg.wandb.mode="disabled"`, `cfg.optuna.n_trials=0`, epochs=1, limited batches
   - `mode=full`: Set `cfg.wandb.mode="online"`, use full configuration
4. **Run Execution**: main.py executes a single run_id passed via CLI (GitHub Actions dispatches multiple runs separately)
5. **WandB Integration**: All metrics logged to WandB; train.py does NOT output JSON to stdout or save results.json
6. **Independent Evaluation**: evaluate.py runs separately, fetches data from WandB API, generates all figures


{% if code_validation %}
## Code Validation Feedback
{% set is_ready, issue = code_validation %}
{% if not is_ready and issue %}
**Previous Validation Issue**: {{ issue }}
**Action Required**: Address this issue in the implementation.

**Previous Code (for reference)**:
{{ research_session.current_iteration.experimental_design.experiment_code.model_dump() | tojson }}

Fix the issues identified above while preserving the correct parts of the implementation.
{% endif %}
{% endif %}

# Experimental Environment
{{ runner_type_prompt }}

# Hypothesis
{{ research_session.hypothesis }}

# Current Research Method
{{ research_session.current_iteration.method }}

# Experimental Design
- Summary: {{ research_session.current_iteration.experimental_design.experiment_summary }}
- Evaluation metrics: {{ research_session.current_iteration.experimental_design.evaluation_metrics }}

# Experiment Runs
{% for run in research_session.current_iteration.experiment_runs %}
- Run ID: {{ run.run_id }}
  Method: {{ run.method_name }}
  Model: {{ run.model_name }}
  Dataset: {{ run.dataset_name }}
  Config File: config/runs/{{ run.run_id }}.yaml
  {% if run.run_config %}
  Config Content:
  ```yaml
  {{ run.run_config }}
  ```
  {% endif %}
{% endfor %}

# External Resources (Use these for implementation)
{% if research_session.current_iteration.experimental_design.external_resources and research_session.current_iteration.experimental_design.external_resources.hugging_face %}
**HuggingFace Models:**
{% for model in research_session.current_iteration.experimental_design.external_resources.hugging_face.models %}
- ID: {{ model.id }}
{% if model.extracted_code %}
- Code: {{ model.extracted_code }}
{% endif %}
{% endfor %}

**HuggingFace Datasets:**
{% for dataset in research_session.current_iteration.experimental_design.external_resources.hugging_face.datasets %}
- ID: {{ dataset.id }}
{% if dataset.extracted_code %}
- Code: {{ dataset.extracted_code }}
{% endif %}
{% endfor %}
{% endif %}

Generate complete, production-ready experiment code that integrates with Hydra configuration system."""
