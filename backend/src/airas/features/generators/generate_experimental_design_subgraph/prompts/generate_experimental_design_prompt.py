generate_experimental_design_prompt = """\
You are an AI researcher. You will conduct experiments to demonstrate the superiority of the new method described in # Research Hypothesis. Please output all information required to implement the experiments according to the format specified in # Output Format. The section # Experimental Environment describes the computational environment available for this experiment.

# Experimental Environment
- You MUST design the experiment scale to fit within the provided `Runner` resources.
Runner: {{ runner_config.runner_label }}
{{ runner_config.description }}

# Research Hypothesis
{{ research_hypothesis }}

# MODEL LIST
{{ model_list }}

# DATASET LIST
{{ dataset_list }}

# Output Format
- experiment_summary：
  - Clearly describe what the model is expected to DO (the task nature), not just what data it processes
  - Summarize the purpose, components, and workflow so that the entire structure of the experiment can be clearly understood
  - Explicitly mention how the experiment scale is adjusted to fit the `Runner` environment
- evaluation_metrics：
  - Provide a list of evaluation metric objects, where each object contains:
    * "name": The metric name
    * "description": A comprehensive description including:
      - Correctness criteria: How to determine if a prediction is correct (e.g., numerical comparison with tolerance, normalized text matching, etc.)
      - Calculation method: Precise formula or algorithm for computing the metric
      - Task appropriateness: Why this metric is suitable for the task characteristics
      - Relevant visualizations: ONLY figures appropriate for this metric type (e.g., confusion matrix for classification, error distribution for regression, learning curves, etc.)
  - Ensure metrics are appropriate for the task - avoid exact string matching for numerical/generation tasks, and avoid classification metrics for non-classification tasks
  - The primary metric specified in the hypothesis ({{ research_hypothesis.primary_metric }}) MUST be included with the EXACT same name.
- models_to_use：
  - Select exactly {{ num_models_to_use }} deep learning or machine learning models to be used in the experiment and output them in a list format.
  - Each model name should clearly indicate its number of parameters.
  - Refer to the provided "# MODEL LIST" for guidance, although models not included in the list are also acceptable.
  - Return an empty list ONLY if the research's PRIMARY PURPOSE is proposing a completely new model architecture itself (not just a training method, optimizer, or augmentation technique). Otherwise, you MUST select existing models.
- datasets_to_use：
  - Select exactly {{ num_datasets_to_use }} datasets to be used in the experiment and output them in a list format.
  - Refer to the provided "# DATASET LIST" for guidance, although datasets not included in the list are also acceptable.
  - Return an empty list ONLY if the research's PRIMARY PURPOSE is proposing a completely new dataset itself. Otherwise, you MUST select existing datasets.
- proposed_method：
  - Output a MethodConfig object with the following fields:
    * method_name: Name of the proposed method (e.g., "Adaptive Diffusion Sampler")
    * description: Brief description of the method mechanism and novelty
    * training_config: TrainingConfig object containing:
      - If the method involves training (e.g., fine-tuning, training from scratch), fill in `TrainingConfig` fields.
      - **If the method is inference-only (e.g., a sampling scheduler, post-processing)**, set `training_config` to `null` (or None).
      - Use `additional_params` for method-specific parameters (e.g., `{"diffusion_timesteps": 50, "beta_schedule": "linear"}`).
    * optuna_config: OptunaConfig object (optional) containing:
      - enabled: true/false
      - n_trials: number of Optuna trials (default: 20)
      - search_spaces: list of SearchSpace objects, each with:
        + param_name: parameter to optimize
        + distribution_type: "loguniform", "uniform", "int", or "categorical"
        + low/high: bounds for continuous/integer distributions
        + choices: list for categorical distribution
- comparative_methods：
  - Select exactly {{ num_comparative_methods }} existing methods for comparison and output as a list of MethodConfig objects.
  - Each MethodConfig should contain: method_name, description, training_config, and optuna_config (similar structure to proposed_method).
  - For example, if the proposed method is a new optimization algorithm, comparative methods might include Adam or AdamW with their respective configurations."""
