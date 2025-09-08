generate_experiment_strategy_prompt = """\
You are a cutting-edge AI researcher. Based on the instructions below, please design an experimental plan to demonstrate the effectiveness of the new research idea described in # New Methods.

# Instructions
- Propose up to three experimental strategies to verify the effectiveness of the new research idea.
- Each experiment should be realistic and take into account the experimental environment.
- For each experiment, also describe what the results would ultimately demonstrate.
- The proposed experiments must clearly highlight the effectiveness of the method.
- Consider experiments that showcase the strengths of the method from multiple perspectives.

{% if consistency_feedback %}
- **Important**: Address the following feedback from previous experimental consistency evaluation:
{{ consistency_feedback }}
- Specifically improve the experimental design to resolve these consistency issues.
{% endif %}

# Experimental Environment
{{ runner_type_prompt }}

# Current Research Method (Target for Experiment Design)
{{ new_method.method }}

---
# Reference Information from Previous Iteration
{% if new_method.iteration_history %}
**Previous Experimental Design**:
- Strategy: {{ new_method.iteration_history[-1].experimental_design.experiment_strategy }}
- Details: {{ new_method.iteration_history[-1].experimental_design.experiment_details }}

{% if generated_file_contents %}
**Previous Generated Code Files**:
{% for filename, content in generated_file_contents.items() %}
### {{ filename }}
```python
{{ content }}
```
{% endfor %}
{% endif %}

Build upon what worked and address what didn't work to improve the consistency score.
{% else %}
*No previous iteration available*
{% endif %}
---"""
