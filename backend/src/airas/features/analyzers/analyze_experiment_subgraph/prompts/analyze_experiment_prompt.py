analyze_experiment_prompt = """\
You are an expert in machine learning research.

Your task is to analyze the experimental results and generate a comprehensive analysis report that demonstrates the effectiveness of the proposed method.

# Instructions
1. Analyze the experimental results from all experiments
2. Synthesize findings to demonstrate the overall effectiveness of the proposed method
3. Highlight how the proposed method outperforms baselines
4. Reference specific metrics and experimental outcomes
5. Generate a detailed analysis report

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

# Experimental Results
{% if experimental_results %}
{% if experimental_results.metrics_data %}
## Metrics Data
{{ experimental_results.metrics_data | tojson(indent=2) }}
{% endif %}

{% if experimental_results.figures %}
## Figures
{% for figure in experimental_results.figures %}
- {{ figure }}
{% endfor %}
{% endif %}

{% else %}
No experimental results available yet.
{% endif %}

# Task
Please summarize the experimental results in detail as an "analysis_report", based on the experimental setup and outcomes. Also, include whether the new method demonstrates a clear advantage over baselines.
"""
