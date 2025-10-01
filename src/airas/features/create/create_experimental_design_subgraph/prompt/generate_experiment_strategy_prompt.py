generate_experiment_strategy_prompt = """\
You are a cutting-edge AI researcher. Based on the new research method described in # New Methods, please design an overall experimental strategy that will be applied across all experiments to demonstrate the effectiveness of this method.

# Instructions
- Define a comprehensive experimental strategy that will guide multiple experiments.
- This strategy should be common to all experiments that will be conducted.
- The strategy should address:
    - What aspects of the proposed method need to be validated (e.g., performance improvement, efficiency, robustness, generalization)
    - What types of comparisons are necessary (e.g., baselines, ablations, state-of-the-art methods)
    - What experimental angles will be used to validate the claims (e.g., quantitative performance, qualitative analysis, computational cost)
    - How to demonstrate the method's effectiveness from multiple perspectives
    - What validation criteria will determine success
- The strategy should be realistic and take into account the experimental environment.
- Focus on the overall approach rather than specific experiment details (which will be defined in subsequent steps).

## Output Format
Please provide:
- experiment_strategy: A comprehensive strategy statement that describes the overall approach for validating the proposed method across all experiments

# Experimental Environment
{{ runner_type_prompt }}

# Current Research Method (Target for Experiment Design)
{{ new_method.method }}

---
{% if consistency_feedback %}
- **Important**: Address the following feedback from previous experimental consistency evaluation:
{{ consistency_feedback }}
- Specifically improve the experimental strategy to resolve these consistency issues.
{% endif %}

# Reference Information from Previous Iteration
{% if new_method.iteration_history %}
**Previous Experimental Design**:
- Strategy: {{ new_method.iteration_history[-1].experimental_design.experiment_strategy }}
- Experiments: {{ new_method.iteration_history[-1].experimental_design.experiments | tojson }}

Build upon what worked and address what didn't work to improve the consistency score.
{% endif %}
"""
