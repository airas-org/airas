generate_base_code_prompt = """\
You are a cutting-edge AI researcher preparing the COMMON CORE FOUNDATION for experiments that will ensure consistency across all experimental variations.

This step generates the **COMMON CORE FOUNDATION** for experiments that will ensure consistency across all experimental variations.

**Current Task**: Generate common base logic, evaluation framework, and infrastructure with placeholders for specific datasets/models
**Next Step**: A subsequent step will derive specific experiments by replacing placeholders with actual datasets/models

Based on the research method in # Current Research Method and experimental design in # Experimental Design, generate the foundational code that will serve as the common base for ALL experimental variations.

# Instructions: Common Core Foundation Generation

## Core Requirements
- **COMMON EVALUATION LOGIC**: Implement consistent evaluation metrics, result collection, and comparison logic that will work across all experimental variations
- **CORE ALGORITHM IMPLEMENTATION**: Implement the main method/algorithm with full functionality
- **INFRASTRUCTURE CODE**: Complete training loops, model saving/loading, configuration handling, and result visualization
- **PLACEHOLDER STRATEGY**: Use clear, descriptive placeholders for dataset-specific and model-specific components that will be replaced in subsequent steps
- **CONSISTENCY FRAMEWORK**: Ensure all experiments will use identical evaluation criteria, metrics calculation, and result formatting

## Placeholder Guidelines
- Use descriptive placeholder names like `DATASET_PLACEHOLDER`, `MODEL_PLACEHOLDER`, `SPECIFIC_CONFIG_PLACEHOLDER`
- Include comments explaining what will be replaced: `# PLACEHOLDER: Will be replaced with specific dataset loading logic`
- Ensure placeholders are easily identifiable and replaceable in the next phase
- Keep the base logic intact - only dataset/model-specific parts should be placeholders

## Implementation Requirements
- **ZERO PLACEHOLDER POLICY FOR CORE LOGIC**: Generate complete, production-ready base framework. NO placeholders for training loops, evaluation logic, or result processing.
- **COMPLETE IMPLEMENTATION**: Every base component must be fully functional. No "omitted for brevity", no "simplified version" for base logic.
- **PUBLICATION-READY INFRASTRUCTURE**: Framework must produce actual publication-worthy results when datasets/models are specified
- **USE PYTORCH EXCLUSIVELY** as the deep learning framework
- **COMPLETE DATA PIPELINE FRAMEWORK**: Implement data loading and preprocessing pipeline with placeholders for specific datasets
- **COMPREHENSIVE EXPERIMENT INFRASTRUCTURE**: Full-scale experiment framework with sufficient training epochs, proper validation splits, and thorough evaluation metrics
- **STRUCTURED PLACEHOLDER APPROACH**: Use well-defined placeholders for dataset/model specifics while ensuring base logic is complete and functional

## Results Documentation Requirements
- Save each experiment's results as separate JSON files in the `.research/iteration{{ experiment_iteration }}/` directory and print each JSON contents to standard output for verification.

## Standard Output Content Requirements
- Experiment description: Before printing experimental results, the standard output must include a detailed description of the experiment.
- Experimental numerical data: All experimental data obtained in the experiments must be output to the standard output.
- Names of figures summarizing the numerical data

## Figure Output Requirements
- Experimental results must always be presented in clear and interpretable figures without exception.
- Use matplotlib or seaborn to output the results (e.g., accuracy, loss curves, confusion matrix).
- Numeric values must be annotated on the axes of the graphs.
- For line graphs, annotate significant values (e.g., the final or best value) to highlight key findings. For bar graphs, annotate the value above each bar.
- Include legends in the figures.
- All figures must be saved in .pdf format (e.g., using plt.savefig("filename.pdf", bbox_inches="tight")).
  - Do not use .png or any other formats—only .pdf is acceptable for publication quality.
- Please save all images output from the experiment in the `.research/iteration{{ experiment_iteration }}/images/` directory.

## Figure Naming Convention
File names must follow the format: `<figure_topic>[_<condition>][_pairN].pdf`
- `<figure_topic>`: The main subject of the figure (e.g., training_loss, accuracy, inference_latency)
- `_<condition>` (optional): Indicates model, setting, or comparison condition (e.g., amict, baseline, tokens, multimodal_vs_text)
- `_pairN` (optional): Used when presenting figures in pairs (e.g., _pair1, _pair2)
- For standalone figures, do not include _pairN.

{% if secret_names %}
- Environment Variables: The following environment variables are available: {{ secret_names|join(', ') }}
{% endif %}

## Command Line Interface
The generated main.py must support:
```bash
# Smoke test with any dataset/model combination
uv run python -m src.main --smoke-test

# Full experiment with any dataset/model combination
uv run python -m src.main --full-experiment
```

## Output Structure
Generate complete foundational code for these files ONLY. Do not create any additional files beyond this structure:

### Script Structure (ExperimentCode format)
Your output must contain EXACTLY these 7 files with NO additional files:
- `src/train.py`: Core training logic with algorithm implementation and placeholder data loading
- `src/evaluate.py`: Universal evaluation framework that works across all experimental variations
- `src/preprocess.py`: Common preprocessing pipeline with dataset placeholders
- `src/main.py`: Main execution script with flexible configuration system
- `pyproject.toml`: Complete project dependencies
- `config/smoke_test.yaml`: Base configuration template for quick validation
- `config/full_experiment.yaml`: Base configuration template for full experiments

### Key Implementation Focus Areas
1. **Evaluation Consistency**: Identical metrics calculation, result formatting, and comparison logic
2. **Algorithm Core**: Full implementation of the proposed method with proper abstraction
3. **Result Infrastructure**: Consistent figure generation, data saving, and output formatting
4. **Configuration Flexibility**: System that can handle different datasets/models via configuration

{% if base_code_validation %}
## Core code Validation Feedback
{% set is_ready, issue = base_code_validation %}
{% if not is_ready and issue %}
**Previous Validation Issue**: {{ issue }}
**Action Required**: Address this by ensuring the base framework provides a solid foundation for experimental implementations.
{% endif %}
{% endif %}

# Experimental Environment
{{ runner_type_prompt }}

# Current Research Method (Target for Experiment Design)
{{ new_method.method }}

# Experimental Design
- Strategy: {{ new_method.experimental_design.experiment_strategy }}
- Details: {{ new_method.experimental_design.experiment_details }}

{% if consistency_feedback %}
## Consistency Feedback
**Critical**: Address the following consistency requirements in your base framework:
{{ consistency_feedback }}

Ensure your foundational code addresses these consistency issues across all future experimental variations.
{% endif %}

# Reference Information from Previous Iteration
{% if new_method.iteration_history %}
## Previous Experimental Design
- Strategy: {{ new_method.iteration_history[-1].experimental_design.experiment_strategy }}
- Details: {{ new_method.iteration_history[-1].experimental_design.experiment_details }}
{% endif %}

Remember: This is the FOUNDATION that will ensure ALL experimental variations are conducted on the same rigorous, consistent basis. Focus on creating robust base logic with strategic placeholders for dataset/model specifics."""
