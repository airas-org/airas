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
  - Describe the overall implementation details of the experiment. Summarize the purpose, components, and workflow so that the entire structure of the experiment can be clearly understood.
- evaluation_metrics：
  - List all evaluation metrics used in this experiment, including only their names, in a list format. (e.g., Accuracy AUC ROC, F1 Score, RMSE, BLEU, ROUGE, etc.)
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
