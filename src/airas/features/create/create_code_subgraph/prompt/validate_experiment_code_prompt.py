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
   - CLI interface matches: `uv run python -u -m src.main run={run_id} results_dir={path}`

3. **Complete Data Pipeline**:
   - Full data loading and preprocessing implementation
   - Dataset-specific preprocessing is properly implemented
   - No placeholder dataset loading code
   - Proper error handling for data operations

4. **Model Implementation**:
   - Complete model architectures for baseline, proposed, and ablation methods
   - All models implemented from scratch (no placeholders)
   - Model-specific configurations correctly applied
   - Proper PyTorch usage throughout

5. **File Structure Compliance**:
   - Contains EXACTLY these required files:
     * `src/train.py`
     * `src/evaluate.py`
     * `src/preprocess.py`
     * `src/model.py`
     * `src/main.py`
     * `pyproject.toml`
     * `config/config.yaml`
   - No missing files from the structure
   - All functionality contained within specified files

6. **Structured Logging**:
   - train.py prints JSON-formatted metrics with `run_id` field using `print(json.dumps({...}))`
   - evaluate.py prints JSON-formatted comparison results to stdout
   - main.py redirects subprocess stdout/stderr to `{results_dir}/{run_id}/stdout.log` and `stderr.log`
   - Logs are forwarded to main process stdout/stderr for GitHub Actions capture

7. **Configuration Files**:
   - config/config.yaml contains list of all experiment run_ids
   - NOTE: config/run/{run_id}.yaml files are provided separately in the "Experiment Runs" section below (not in ExperimentCode)
   - The generated code must properly reference these config files via Hydra
   - All run configurations match the experiment_runs provided
   - Optuna search spaces are properly defined if applicable

8. **Evaluation and Figures** (if WandB not used):
   - Figure generation with proper formatting (PDF output to `{results_dir}/images/`)
   - Figures include legends, annotations, and proper labels
   - Uses `plt.tight_layout()` before saving
   - Consistent result formatting and comparison logic

9. **WandB Integration** (if WandB is used):
   - Proper WandB initialization with entity/project from config
   - Metrics logged to WandB during training
   - WandB run URL printed to stdout
   - Metadata saved to `.research/iteration{experiment_iteration}/wandb_metadata.json`
   - Figures uploaded as WandB artifacts

10. **Immediate Executability**:
    - Code can be run immediately without modifications
    - All imports and dependencies properly specified in pyproject.toml
    - No missing external resources or undefined variables
    - Proper module structure for `uv run python -m src.main` execution

## Detection of Common Issues
Flag the following problems if found:

- **Incomplete Implementation**: TODO, PLACEHOLDER, pass, ..., or any placeholder patterns
- **Truncation**: Code sections that appear shortened or simplified inappropriately
- **Missing Functionality**: Expected features not implemented
- **Configuration Issues**: Missing or incomplete run configs
- **Import Errors**: Missing dependencies or incorrect import statements
- **Not Executable**: Code that cannot be run immediately
- **Inconsistent Structure**: Files not matching required structure
- **Logging Issues**: Missing or incorrect JSON logging format

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
