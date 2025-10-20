validate_experiment_code_prompt = """\
You are an AI code reviewer validating production-ready experiment code for research papers.

Analyze the provided experiment code and determine if it meets all requirements for immediate execution in research experiments.

# Instructions

## Core Validation Criteria
Check if the generated experiment code meets ALL of the following requirements:

1. **Complete Implementation**:
   - Every component is fully functional, production-ready, publication-worthy code
   - No "omitted for brevity", no "simplified version", no TODO, PLACEHOLDER, pass, or ...
   - All functions and classes are completely implemented
   - No truncated code sections or incomplete implementations

2. **Hydra Integration**:
   - Uses Hydra to manage all experiment configurations from `config/run/*.yaml` files
   - All parameters are loaded from run configs dynamically
   - Proper configuration structure with run_id, method, model, dataset, training, and optuna sections
   - CLI interface matches:
     * Training: `uv run python -u -m src.main run={run_id} results_dir={path}`
     * Evaluation: `uv run python -m src.evaluate results_dir={path} run_ids='["run-1", "run-2", ...]'` (independent execution)
   - Supports trial_mode=true flag for lightweight validation runs (automatically disables WandB)

3. **Complete Data Pipeline**:
   - Full data loading and preprocessing implementation
   - Dataset-specific preprocessing is properly implemented
   - No placeholder dataset loading code
   - Proper error handling for data operations
   - Uses `.cache/` as the cache directory for all datasets and models

4. **Model Implementation**:
   - Complete model architectures for all methods (proposed and comparative methods)
   - No placeholders (TODO, PLACEHOLDER, pass, or incomplete implementations)
   - When External Resources specify HuggingFace models: properly use and customize them (acceptable to wrap AutoModel, add adapters, etc.)
   - When no external models specified: implement architectures from scratch using PyTorch primitives
   - Model-specific configurations correctly applied
   - Proper PyTorch usage throughout

5. **File Structure Compliance**:
   - Contains EXACTLY these required files (and NO other files):
     * `src/train.py`
     * `src/evaluate.py`
     * `src/preprocess.py`
     * `src/model.py`
     * `src/main.py`
     * `pyproject.toml`
     * `config/config.yaml`
   - NO additional files (e.g., NO `src/__init__.py`, NO `setup.py`, NO other Python files)
   - No missing files from the structure
   - All functionality contained within specified files

6. **WandB Integration**:
   - train.py initializes WandB and logs ALL metrics using `wandb.log()`
   - trial_mode automatically disables WandB (sets wandb.mode=disabled)
   - NO results.json or stdout JSON dumps in train.py
   - config/config.yaml contains mandatory WandB settings (entity/project)

7. **Configuration Files**:
   - The generated code properly references config files via Hydra
   - NOTE: config/run/{run_id}.yaml files are provided separately (not in ExperimentCode)
   - All run configurations match the experiment_runs provided
   - Optuna search spaces are properly defined if applicable

8. **Evaluation Script Independence**:
   - evaluate.py is executed independently via `uv run python -m src.evaluate results_dir={path} run_ids='["run-1", "run-2"]'`
   - Accepts `run_ids` parameter as JSON string list (parse with `json.loads(args.run_ids)`)
   - main.py DOES NOT call evaluate.py
   - evaluate.py retrieves ALL data from WandB API using `wandb.Api()` (not from local files)
   - **STEP 1: Per-Run Processing** (for each run_id):
     * Export run-specific metrics to: `{results_dir}/{run_id}/metrics.json`
     * Generate run-specific figures (learning curves, confusion matrices) to: `{results_dir}/{run_id}/`
     * Each run should have its own subdirectory with its metrics and figures
   - **STEP 2: Aggregated Analysis** (after processing all runs):
     * Export aggregated metrics to: `{results_dir}/comparison/aggregated_metrics.json`
     * Compute secondary/derived metrics (e.g., improvement rate: (proposed - baseline) / baseline)
     * Generate comparison figures to: `{results_dir}/comparison/`
     * Cross-run comparison charts (bar charts, box plots)
     * Performance metrics tables
     * Statistical significance tests
   - Proper figure quality: legends, annotations, tight_layout
   - Follows naming convention: `<figure_topic>[_<condition>][_pairN].pdf`
   - train.py and main.py generate NO figures
   - evaluate.py cannot run in trial_mode (no WandB data available when WandB disabled)

9. **Trial Mode Implementation**:
   - trial_mode=true flag properly reduces computational load
   - Training: epochs=1, batches limited to 1-2, Optuna disabled (n_trials=0), small evaluation subset
   - WandB automatically disabled in trial_mode (wandb.mode=disabled)
   - Purpose: Fast validation that code runs without errors

## Output Format
Respond with a JSON object containing:
- `is_code_ready`: boolean - true if ALL criteria are met, false otherwise
- `code_issue`: string - specific issues found if any criteria are not met, focusing on what needs to be fixed

# Current Research Method
{{ new_method.method }}

# Experimental Design
- Strategy: {{ new_method.experimental_design.experiment_summary }}
- Proposed Method: {{ new_method.experimental_design.proposed_method }}
- Evaluation Metrics: {{ new_method.experimental_design.evaluation_metrics }}

# Experiment Runs
{% for run in new_method.experiment_runs %}
- Run ID: {{ run.run_id }}
  Method: {{ run.method_name }}
  Model: {{ run.model_name }}
  Dataset: {{ run.dataset_name }}
  {% if run.run_config %}
  Config Content:
  ```yaml
  {{ run.run_config }}
  ```
  {% endif %}
{% endfor %}

# Generated Experiment Code (To be validated)
{{ new_method.experimental_design.experiment_code | tojson }}

Analyze the experiment code thoroughly. Ensure it is complete, executable, and ready for publication-quality research experiments."""
