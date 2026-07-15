analyze_experiment_prompt = """\
You are an expert in machine learning research.

Your task is to analyze the experimental results and generate a comprehensive analysis report.

# Instructions
1. For each evaluation metric, report the numeric values for the proposed method and each baseline.
2. For metrics where the proposed method outperforms baselines, explain why — what property of the method, data, or task leads to the advantage.
3. For metrics where the proposed method underperforms or matches baselines, explain why — identify the root cause (e.g., insufficient data, inappropriate model capacity, overfitting, task mismatch).
4. Assess whether the results are consistent with the research hypothesis and explain any discrepancies.
5. Summarize the overall strengths and weaknesses of the proposed method based on the above analysis.

# Research Hypothesis
{{ research_hypothesis.method }}

{% if experimental_design %}
# Experimental Design

{% if experimental_design.experiment_summary %}
## Experiment Summary
{{ experimental_design.experiment_summary }}
{% endif %}

{% if experimental_design.evaluation_metrics %}
## Evaluation Metrics
{% for metric in experimental_design.evaluation_metrics %}
- **{{ metric.name }}**: {{ metric.description }}
{% endfor %}
{% endif %}

{% if experimental_design.proposed_method %}
## Proposed Method
**{{ experimental_design.proposed_method.method_name }}**: {{ experimental_design.proposed_method.description }}
{% if experimental_design.proposed_method.training_config %}
### Training Configuration
- Learning Rate: {{ experimental_design.proposed_method.training_config.learning_rate }}
- Batch Size: {{ experimental_design.proposed_method.training_config.batch_size }}
- Epochs: {{ experimental_design.proposed_method.training_config.epochs }}
{% if experimental_design.proposed_method.training_config.optimizer %}
- Optimizer: {{ experimental_design.proposed_method.training_config.optimizer }}
{% endif %}
{% endif %}
{% endif %}

{% if experimental_design.comparative_methods %}
## Comparative Methods
{% for method in experimental_design.comparative_methods %}
- **{{ method.method_name }}**: {{ method.description }}
{% endfor %}
{% endif %}

{% if experimental_design.models_to_use %}
## Models Used
{% for model in experimental_design.models_to_use %}
- {{ model }}
{% endfor %}
{% endif %}

{% if experimental_design.datasets_to_use %}
## Datasets Used
{% for dataset in experimental_design.datasets_to_use %}
- {{ dataset }}
{% endfor %}
{% endif %}
{% endif %}

{% if experiment_code %}
# Experiment Code
{{ experiment_code }}
{% endif %}

# Experimental Results
{% if experimental_results %}
{% if experimental_results.metrics_data %}
## Metrics Data
{{ experimental_results.metrics_data | tojson(indent=2) }}
{% endif %}

{% else %}
No experimental results available yet.
{% endif %}

# Task
Generate an "analysis_report" following the instructions above.
"""
