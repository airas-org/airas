generate_run_config_prompt = """\
You are an AI research assistant tasked with generating Hydra configuration files for experiment runs.

# Task
Generate individual YAML configuration files for each experiment run. These configs will be used by Hydra to configure specific experimental variations.

# Input Information

## Research Method
{{ new_method.method }}

## Experimental Design
{{ new_method.experimental_design }}

## Experiment Runs
{% for run in new_method.experiment_runs %}
- Run ID: {{ run.run_id }}
  Method: {{ run.method_name }}
  Model: {{ run.model_name }}
  Dataset: {{ run.dataset_name }}
{% endfor %}

# Requirements

## Configuration Structure
Each run configuration should include:
- run_id: Unique identifier for this run
- method: The method name (baseline, proposed, ablation, etc.)
- model: Model-specific parameters (name, architecture details, hyperparameters)
- dataset: Dataset-specific parameters (name, preprocessing settings, split ratios)
- training: Training hyperparameters (learning rate, batch size, epochs, optimizer settings)
- optuna: Hyperparameter search space definition for Optuna optimization
  - Define search spaces for key hyperparameters using Optuna's suggest methods
  - Example: learning_rate: [1e-5, 1e-3], batch_size: [16, 32, 64]
- Any other experiment-specific settings

## Format
- Generate one YAML configuration per experiment run
- Ensure valid YAML syntax
- Use meaningful parameter values based on the research method and experimental design

## Example Configuration
```yaml
run_id: baseline_bert_imdb
method: baseline
model:
  name: bert-base-uncased
  hidden_size: 768
  num_layers: 12
dataset:
  name: imdb
  max_length: 512
  batch_size: 32
training:
  learning_rate: 2e-5
  epochs: 3
  optimizer: adamw
  warmup_steps: 500
optuna:
  n_trials: 20
  search_space:
    learning_rate:
      type: loguniform
      low: 1e-5
      high: 1e-3
    batch_size:
      type: categorical
      choices: [16, 32, 64]
```

# Experimental Environment
{{ runner_type_prompt }}

# Instructions
1. Generate one YAML configuration for each experiment run listed above
2. Ensure configurations reflect the differences between baseline, proposed, and ablation methods
3. Use appropriate hyperparameters based on the experimental design
4. Include Optuna search space if hyperparameter optimization is beneficial for the experiment
5. For Optuna search spaces, use appropriate distribution types:
   - loguniform: For learning rates, regularization parameters
   - uniform: For dropout rates, weight decay
   - int: For hidden dimensions, number of layers
   - categorical: For discrete choices like batch size, optimizer type

Generate the configurations now:"""
