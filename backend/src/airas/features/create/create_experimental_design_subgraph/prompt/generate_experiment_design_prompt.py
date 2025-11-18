generate_experiment_design_prompt = """\
You are an AI researcher. You will conduct experiments to demonstrate the superiority of the new method described in # New Methods. Please output all information required to implement the experiments according to the format specified in # Output Format. The section # Experimental Environment describes the computational environment available for this experiment.

# Experimental Environment
{{ runner_type_prompt }}

# Hypothesis
{{ research_session.hypothesis }}

# Current Research Method
{{ research_session.current_iteration.method }}

# MODEL LIST
{{ model_list }}

# DATASET LIST
{{ dataset_list }}

# Output Format
- experiment_summary：
  - Clearly describe what the model is expected to DO (the task nature), not just what data it processes
  - Summarize the purpose, components, and workflow so that the entire structure of the experiment can be clearly understood
- evaluation_metrics：
  - Provide a list of evaluation metric objects, where each object contains:
    * "name": The metric name
    * "description": A comprehensive description including:
      - Correctness criteria: How to determine if a prediction is correct (e.g., numerical comparison with tolerance, normalized text matching, etc.)
      - Calculation method: Precise formula or algorithm for computing the metric
      - Task appropriateness: Why this metric is suitable for the task characteristics
      - Relevant visualizations: ONLY figures appropriate for this metric type (e.g., confusion matrix for classification, error distribution for regression, learning curves, etc.)
  - Ensure metrics are appropriate for the task - avoid exact string matching for numerical/generation tasks, and avoid classification metrics for non-classification tasks
  - The primary metric specified in the hypothesis ({{ research_session.hypothesis.primary_metric }}) MUST be included
- models_to_use：
  - Select {{ num_models_to_use }} deep learning or machine learning models to be used in the experiment and output them in a list format.
  - Each model name should clearly indicate its number of parameters.
  - Refer to the provided “# MODEL LIST” for guidance, although models not included in the list are also acceptable.
  - If the proposed method itself introduces a new model (e.g., a novel architecture), return an empty list and describe the details of the method in new_method.
- datasets_to_use：
  - Select {{ num_datasets_to_use }} datasets to be used in the experiment and output them in a list format.
  - Refer to the provided “# DATASET LIST” for guidance, although datasets not included in the list are also acceptable.
  - If a new dataset is proposed as part of this study, return an empty list and describe its details in new_method.
- proposed_method：
  - Describe the proposed method and its implementation in detail.
  - Clearly state its objectives, theoretical background, components, and algorithmic procedures.
- comparative_methods：
  - Select {{ num_comparative_methods }} existing methods for comparison with the proposed method and output them in a list format.
  - For example, if the proposed method is a new optimization algorithm, comparative methods might include Adam or AdamW.
  - If the proposal is a new LLM architecture, comparative methods might include Llama 4 or Qwen.
- hyperparameters_to_search：
  - Output a list of objects, where each object contains "name" (hyperparameter name) and "range" (search range).
  - For example: [{"name": "learning_rate", "range": "0.001-0.01"}, {"name": "batch_size", "range": "16,32,64"}, {"name": "weight_decay", "range": "0.0001-0.001"}]
  - Search ranges can be expressed as ranges (e.g., "0.001-0.01") or discrete values (e.g., "16,32,64")."""
