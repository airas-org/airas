derive_specific_experiments_prompt = """\
You are a cutting-edge AI researcher specializing experiments from a common base foundation.

**Previous Step (Completed)**: Common base logic and evaluation framework have been generated with placeholders
**Current Task**: Replace placeholders with specific datasets, models, and experimental configurations

Your task is to take the common base foundation code and derive specific experimental variations by replacing placeholders with actual datasets, models, and configurations specified in the experimental design.

# Instructions: Experiment Specialization

## Core Task
- **PLACEHOLDER REPLACEMENT**: Replace all placeholders in the common base code with actual datasets, models, and configurations
- **SPECIALIZATION**: Adapt the generic framework to work with specific experimental requirements
- **REAL IMPLEMENTATIONS**: Convert all placeholder logic to working implementations using actual Hugging Face resources
- **CONFIGURATION COMPLETION**: Fill in specific parameters, hyperparameters, and experimental settings

## Specialization Requirements
- Replace dataset placeholders (like `DATASET_PLACEHOLDER`) with actual Hugging Face dataset loading and preprocessing
- Replace model placeholders (like `MODEL_PLACEHOLDER`) with specific model architectures and configurations
- Fill in exact experimental parameters (epochs, batch sizes, learning rates, etc.) based on experimental design
- Implement dataset-specific evaluation metrics and result formatting
- Complete configuration files with actual experimental values from External Resources
- Ensure all external resources specified in the experimental design are properly integrated

## Key Replacement Areas
1. **Dataset Loading**: Replace `DATASET_PLACEHOLDER` with specific Hugging Face dataset code
2. **Model Architecture**: Replace `MODEL_PLACEHOLDER` with actual model definitions
3. **Configuration Values**: Replace `SPECIFIC_CONFIG_PLACEHOLDER` with real experimental parameters
4. **Preprocessing**: Adapt generic preprocessing to dataset-specific requirements
5. **Evaluation**: Customize evaluation metrics for specific datasets/tasks


# Experimental Environment
{{ runner_type_prompt }}

# Current Research Method
{{ new_method.method }}

# Experimental Design
- Strategy: {{ new_method.experimental_design.experiment_strategy }}
- Details: {{ new_method.experimental_design.experiment_details }}

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


# Common Base Code (Previous Step Output to be specialized)
The common base code generated in the previous step contains the following placeholder patterns that need to be replaced:
- `DATASET_PLACEHOLDER` → Replace with specific Hugging Face dataset loading
- `MODEL_PLACEHOLDER` → Replace with specific model architecture
- `SPECIFIC_CONFIG_PLACEHOLDER` → Replace with actual experimental parameters

Take the foundation code and create complete, specialized experiments using the External Resources specified above."""
