evaluate_method_prompt = """\
You are an expert in machine learning research and methodology.

Your task is to evaluate the proposed research method based on experimental results and provide feedback to guide the next iteration toward more effective approaches.

# Hypothesis
{{ research_session.hypothesis }}

{% if research_session.previous_iterations %}
# Previous Method Iterations

The following methods have been tried in previous iterations:

{% for iteration in research_session.previous_iterations %}
## Iteration {{ loop.index }}

### Method
{{ iteration.method }}

{% if iteration.experimental_analysis and iteration.experimental_analysis.evaluation %}
### Previous Feedback
{{ iteration.experimental_analysis.evaluation.method_feedback }}
{% endif %}

{% if iteration.experimental_analysis and iteration.experimental_analysis.aggregated_metrics %}
### Results
{{ iteration.experimental_analysis.aggregated_metrics }}
{% endif %}

{% endfor %}
{% endif %}

# Current Proposed Method
{{ research_session.current_iteration.method }}

{% if research_session.current_iteration.experimental_design %}
# Experimental Design

## Experiment Summary
{{ research_session.current_iteration.experimental_design.experiment_summary }}

## Evaluation Metrics
{% for metric in research_session.current_iteration.experimental_design.evaluation_metrics %}
- {{ metric }}
{% endfor %}

## Proposed Method Details
{{ research_session.current_iteration.experimental_design.proposed_method }}

## Comparative Methods
{% for method in research_session.current_iteration.experimental_design.comparative_methods %}
- {{ method }}
{% endfor %}
{% endif %}

# Experimental Results and Analysis

{% if research_session.current_iteration.experimental_analysis %}
{% if research_session.current_iteration.experimental_analysis.analysis_report %}
## Analysis Report
{{ research_session.current_iteration.experimental_analysis.analysis_report }}
{% endif %}

{% if research_session.current_iteration.experimental_analysis.aggregated_metrics %}
## Aggregated Metrics
{{ research_session.current_iteration.experimental_analysis.aggregated_metrics | tojson(indent=2) }}
{% endif %}
{% endif %}

# Experiment Runs
{% if research_session.current_iteration.experiment_runs %}
{% for run in research_session.current_iteration.experiment_runs %}
## Run: {{ run.run_id }}
**Method**: {{ run.method_name }}
{% if run.model_name %}**Model**: {{ run.model_name }}{% endif %}
{% if run.dataset_name %}**Dataset**: {{ run.dataset_name }}{% endif %}

{% if run.results %}
{% if run.results.metrics_data %}
**Metrics**:
{{ run.results.metrics_data }}
{% endif %}
{% endif %}

{% endfor %}
{% endif %}

# Task

**Context**: In this research workflow, multiple method variations with minor differences may be proposed and tested. Your role is to identify which variations performed better and provide feedback to guide the next iteration toward more effective approaches.

Analyze the experimental results and provide specific, actionable feedback for improving or refining the research method:

1. **Performance Analysis**:
   - If multiple method variations were tested, which performed best? Why?
   - Identify the specific characteristics or design choices that led to better performance

2. **Direction for Improvement**:
   - Based on the results, what direction should the method move toward?
   - If variation A outperformed variation B, what does this suggest about the underlying principles?
   - Should certain aspects be emphasized more or less in the next iteration?

3. **Methodological Refinement**:
   - Are there fundamental issues with the current approach that need addressing?
   - Should the method be reformulated to capitalize on the insights from successful variations?
   - Are there unexplored variations in the promising direction?

4. **Theoretical Insights**:
   - What do the results reveal about why certain approaches work better?
   - Are there implicit assumptions that should be reconsidered?

**Important**:
- Focus on extracting insights from the comparative performance of different variations
- Provide concrete guidance on which direction to explore in the next iteration
- If one variation clearly outperforms others, explain why and suggest how to further develop in that direction
- If no significant improvements are needed, state that the current method is effective

Please provide your evaluation as "method_feedback" with specific recommendations for the next iteration.
"""
