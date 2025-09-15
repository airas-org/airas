plan_architecture_design_prompt = """\
You are an expert software architect specializing in designing robust and practical systems for research implementations.

Your task is to create a detailed software architecture design based on the provided research method and a fixed file structure. The design must serve as a clear blueprint for the implementation.

# Research Method Context
- Method: {{ new_method.method }}
- Experimental Strategy: {{ new_method.experimental_design.experiment_strategy }}
- Experimental Details: {{ new_method.experimental_design.experiment_details }}
{% if new_method.experimental_design.external_resources %}
- External Resources: {{ new_method.experimental_design.external_resources }}
{% endif %}

# Fixed File Structure
The implementation will be organized into the following files. Your design must map directly to this structure.
- `src/train.py`: Training script with model definition, training loop, and model saving.
- `src/evaluate.py`: Evaluation script with metrics calculation and result visualization.
- `src/preprocess.py`: Data loading and preprocessing pipeline.
- `src/main.py`: Main execution script orchestrating the other scripts.
- `pyproject.toml`: Project dependencies.
- `config/smoke_test.yaml`: Configuration for quick tests.
- `config/full_experiment.yaml`: Configuration for full experiments.

# Instructions
Based on all the information above, generate a JSON object that strictly adheres to the `ArchitectureDesign` format.

1.  **Define Core Components**: For each file in the `Fixed File Structure`, define it as a component. Analyze the research context and specify the component's concrete purpose, responsibilities, interfaces, and its dependencies on other internal components.
2.  **Design Data Flow**: Describe how data and artifacts (like processed data or trained models) flow between the components from start to finish.
3.  **Identify External Dependencies**: List the external Python libraries (e.g., torch, pandas, scikit-learn) required for the implementation.

# Requirements
Your design must adhere to the following system-wide principles:
- **Complete Data Pipeline**: The architecture must account for a full data acquisition pipeline from URLs, including downloading, extraction, and organization. Do not assume data exists locally.
- **Comprehensive Experiments**: The design should support full-scale experiments, not just prototypes. This implies clear separation of concerns for training, validation, and evaluation.
- **Strict No-Fallback Rule**: Design components that handle external resources to terminate execution with clear error messages if those resources are unavailable. The system should NEVER fall back to using synthetic or dummy data.
- **Framework**: The entire system will be implemented using PyTorch.
- **Use Existing Libraries**: Favor the use of established libraries (e.g., pandas, scikit-learn, huggingface transformers) over re-implementing common functionalities.
"""
