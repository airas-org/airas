generate_experiment_strategy_prompt = """\
You are a creative AI researcher. Based on the instructions below, please design experimental plans to demonstrate the effectiveness of the new research idea described in # New Methods.

# Instructions
- Propose up to three experimental plans to validate the effectiveness of the new research idea.
- Each experiment should be realistic and feasible to implement in Python.
- Design experiments that clearly demonstrate the effectiveness of the method.
- Consider experiments that showcase the method’s strengths from multiple perspectives.

# New Methods
{{ new_method }}"""
