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
{% if research_hypothesis.open_problems %}
## Open Problems
{{ research_hypothesis.open_problems }}
{% endif %}

## Method
{{ research_hypothesis.method }}

{% if research_hypothesis.primary_metric %}
## Primary Metric
{{ research_hypothesis.primary_metric }}
{% endif %}

{% if research_hypothesis.supporting_metrics %}
## Supporting Metrics
{% for metric in research_hypothesis.supporting_metrics %}
- {{ metric }}
{% endfor %}
{% endif %}

{% if research_hypothesis.expected_result %}
## Expected Result
{{ research_hypothesis.expected_result }}
{% endif %}

{% if research_hypothesis.expected_conclusion %}
## Expected Conclusion
{{ research_hypothesis.expected_conclusion }}
{% endif %}

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
{% else %}
## Metrics Data
NONE PROVIDED. No numeric results reached this prompt. Do not invent any:
state in the report that the metrics are unavailable, and base whatever
analysis you can write on the run output below.
{% endif %}

{% if experimental_results.result_figures %}
## Result Figures
{% for figure in experimental_results.result_figures %}
- {{ figure }}
{% endfor %}
{% endif %}

{% if experimental_results.diagram_figures %}
## Method Diagrams
{% for figure in experimental_results.diagram_figures %}
- {{ figure }}
{% endfor %}
{% endif %}

{% if experimental_results.stdout %}
## Run Output (stdout)
{{ experimental_results.stdout }}
{% endif %}

{% if experimental_results.stderr %}
## Run Errors (stderr)
{{ experimental_results.stderr }}
{% endif %}
{% else %}
No experimental results available yet.
{% endif %}

# Task
Generate an "analysis_report" following the instructions above.
"""
