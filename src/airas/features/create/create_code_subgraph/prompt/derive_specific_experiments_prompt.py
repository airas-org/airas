derive_specific_experiments_prompt = """\
You are a cutting-edge AI researcher generating complete, executable code for research paper experiments.

**Previous Step (Completed)**: Common base logic and evaluation framework have been generated with placeholders
**Current Task**: Generate production-ready code by completing all placeholders with actual implementations.

Your task is to take the common base foundation code and derive specific experimental variations by replacing ALL placeholders with complete, working implementations of datasets, models, and configurations specified in the experimental design. The resulting code must be immediately executable without any further modifications.

# Instructions: Experiment Specialization

## Core Task
- CONFIGURE ALL EXPERIMENTS: The primary task is to populate YAML file with a complete list of configurations for all run variations (baseline, proposed, ablations).
- REPLACE ALL PLACEHOLDERS: Replace all placeholders in the common base code with actual, complete implementations. No TODO, PLACEHOLDER, pass, or ... are allowed.
- IMPLEMENT MODELS: Implement all model architectures corresponding to the variations defined in the YAML file within `src/model.py`.
- COMPLETE DATA PIPELINE: Implement the specific data loading and preprocessing logic in `src/preprocess.py`.
- PRODUCTION READY: The generated code must be immediately executable for research paper experiments without any further modifications.

## Specialization Requirements
- Complete `config/full_experiment.yaml`: This file is the driver of the entire experiment. Define each run variation ({{ current_experiment.run_variations }}) as a separate item in the `runs` list, specifying its unique id, model name, and parameters.
- Complete `config/smoke_test.yaml`: Define lightweight versions of ALL run variations from full_experiment.yaml with reduced epochs/data to quickly validate pipeline integrity.
- Implement all required model architectures in `src/model.py`. The model names in the YAML must correspond to the model registry.
- Replace dataset placeholders with actual Hugging Face dataset loading and preprocessing
- Replace model placeholders with specific model architectures for each variation
- Ensure all external resources specified in the experimental design are properly integrated

## Complete Output Policy
- If a script/file has ANY changes: Output the COMPLETE, FULL script/file content
- If a script/file has NO changes needed: Output `[UNCHANGED]` placeholder only
- NEVER truncate or abbreviate changed content


# Experimental Environment
{{ runner_type_prompt }}

# Current Research Method
{{ new_method.method }}

# Experimental Design
- Strategy: {{ new_method.experimental_design.experiment_strategy }}

# Current Experiment (to generate code for)
- Experiment ID: {{ current_experiment.experiment_id }}
- Description: {{ current_experiment.description }}
- Run Variations: {{ current_experiment.run_variations }}

# Base Code
{{ new_method.experimental_design.base_code }}

# External Resources (Use these to replace placeholders)
{% if new_method.experimental_design.external_resources and new_method.experimental_design.external_resources.hugging_face %}
**HuggingFace Models (Replace MODEL_PLACEHOLDER with these):**
{% for model in new_method.experimental_design.external_resources.hugging_face.models %}
- ID: {{ model.id }}
{% if model.extracted_code %}
- Code: {{ model.extracted_code }}
{% endif %}
{% endfor %}

**HuggingFace Datasets (Replace DATASET_PLACEHOLDER with these):**
{% for dataset in new_method.experimental_design.external_resources.hugging_face.datasets %}
- ID: {{ dataset.id }}
{% if dataset.extracted_code %}
- Code: {{ dataset.extracted_code }}
{% endif %}
{% endfor %}
{% endif %}

{% if experiment_code_validation %}
# Validation Feedback
{% set is_ready, issue = experiment_code_validation %}
{% if not is_ready %}
**Previous Validation Failed**: {{ issue }}
Please address the validation issues and regenerate the affected files while keeping successful files unchanged using [UNCHANGED] markers.
{% endif %}
{% endif %}

Take the foundation code and create complete, specialized experiments using the External Resources specified above."""
