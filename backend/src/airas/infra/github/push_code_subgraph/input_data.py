from airas.core.types.experiment_code import ExperimentCode
from airas.core.types.github import GitHubConfig

push_code_subgraph_input_data = {
    "github_config": GitHubConfig(
        github_owner="auto-res2",
        repository_name="test",
        branch_name="main",
    ),
    "experiment_code": ExperimentCode(
        train_py="# Training script\nprint('Training...')",
        evaluate_py="# Evaluation script\nprint('Evaluating...')",
        main_py="# Main script\nprint('Running...')",
        pyproject_toml="[project]\nname = 'test-experiment'",
        config_yaml="# Config\ndefault: test",
        run_configs={
            "run-1-proposed-model-dataset": """run_id: run-1-proposed-model-dataset
method: proposed
model:
  name: example-model
dataset:
  name: example-dataset
training:
  batch_size: 32
  learning_rate: 0.001
""",
            "run-2-baseline-model-dataset": """run_id: run-2-baseline-model-dataset
method: baseline
model:
  name: example-model
dataset:
  name: example-dataset
training:
  batch_size: 32
  learning_rate: 0.001
""",
        },
    ),
}
