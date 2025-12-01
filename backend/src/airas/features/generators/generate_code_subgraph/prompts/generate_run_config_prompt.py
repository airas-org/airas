generate_run_config_prompt = """\
You are an AI research assistant tasked with generating Hydra configuration files for experiment runs.

# Task
Generate individual YAML configuration files for each experiment run. These configs will be used by Hydra to configure specific experimental variations.

# Input Information

## Research Hypothesis
{{ research_hypothesis }}

## Experimental Design
{{ experimental_design }}

# Instructions for Generating Run Configurations

Based on the experimental design, generate run configurations for all combinations of:
- Models: {{ experimental_design.models_to_use }}
- Datasets: {{ experimental_design.datasets_to_use }}
- Methods:
  - Proposed Method: {{ experimental_design.proposed_method.method_name }}
  - Comparative Methods: {% for method in experimental_design.comparative_methods %}{{ method.method_name }}{% if not loop.last %}, {% endif %}{% endfor %}

# Requirements

## Run ID Naming Convention
Generate unique run_id for each configuration using the format:
`{method_type}-{model_name}-{dataset_name}`

Where:
- method_type: "proposed" for the proposed method, or "comparative-{index}" for comparative methods (e.g., "comparative-1", "comparative-2")
- model_name: Simplified model name (e.g., "bert" for "bert-base-uncased")
- dataset_name: Dataset name

Example: `proposed-bert-imdb`, `comparative-1-roberta-sst2`

## Configuration Structure
Each run configuration should include:
- run_id: Unique identifier (following naming convention above)
- method: The method name from the experimental design
- model: Model-specific parameters
  - name: Model identifier
  - Use training_config from the corresponding MethodConfig if available
- dataset: Dataset-specific parameters
  - name: Dataset identifier
  - preprocessing settings, split ratios
- training: Training hyperparameters
  - Use training_config from the corresponding MethodConfig if available
  - Otherwise use reasonable defaults based on the experimental design
  - Include: learning_rate, batch_size, epochs, optimizer, etc.
- optuna: Hyperparameter search space (if optuna_config is defined in MethodConfig)
  - n_trials: From MethodConfig.optuna_config.n_trials
  - search_spaces: From MethodConfig.optuna_config.search_spaces

## Example Configuration
```yaml
run_id: proposed-bert-imdb
method: proposed-method-v1
model:
  name: bert-base-uncased
  hidden_size: 768
dataset:
  name: imdb
  max_length: 512
training:
  learning_rate: 2e-5
  batch_size: 32
  epochs: 3
  optimizer: adamw
  warmup_steps: 500
optuna:
  n_trials: 20
  search_spaces:
    - param_name: learning_rate
      distribution_type: loguniform
      low: 1e-5
      high: 1e-3
    - param_name: batch_size
      distribution_type: categorical
      choices: [16, 32, 64]
```

# Experimental Environment
Runner: {{ experimental_design.runner_config.runner_label }}
{{ experimental_design.runner_config.description }}

# Final Instructions
1. Generate one YAML configuration for EACH combination of (method, model, dataset)
2. Use the MethodConfig's training_config and optuna_config when available
3. Ensure configurations reflect the differences between proposed and comparative methods
4. Follow the run_id naming convention strictly
5. The `run_id` field in RunConfigOutput MUST exactly match the `run_id:` field at the top of the YAML content.
6. Output a list of RunConfigOutput objects with run_id and run_config_yaml fields

Generate all configurations now:"""
