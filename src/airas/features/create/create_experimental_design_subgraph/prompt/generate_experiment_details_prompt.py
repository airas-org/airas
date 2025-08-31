generate_experiment_details_prompt = """\
You are a creative AI researcher. Based on the new method described in # New Methods and the experimental policy outlined in # Experiment Strategy, please follow the instructions below and elaborate on the experimental details.

# Instructions
- Please respond to each experimental item listed in Experiment Strategy.
- Explain the details of each experiment as thoroughly as possible. It is acceptable if the output is long.
- If you have any examples of experimental code, please include them.
- Use experimental methods that enhance the reliability of your research.
- Ensure that the experimental contents do not overlap excessively. If multiple verification items can be addressed within a single experiment, please integrate them accordingly.
- Design your experiments under the assumption that PyTorch will be used for implementation.
- Utilize existing Python libraries as much as possible, and avoid implementing things from scratch.

{% if consistency_feedback %}
- **Important**: Address the following feedback from previous experimental consistency evaluation:
{{ consistency_feedback }}
- Specifically improve the experimental details to resolve these consistency issues.
{% endif %}

# New Methods
{{ new_method }}
# Experiment Strategy
{{ experiment_strategy }}"""
