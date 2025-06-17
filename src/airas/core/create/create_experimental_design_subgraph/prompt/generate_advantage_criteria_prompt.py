generate_advantage_criteria_prompt = """\
Please follow the instructions below and tell us about your experimental plan to demonstrate the superiority of the “New Method”.
- Please tell us up to three things you would like to experiment with.
- Please make sure that the things you would like to experiment with are realistic and possible to code in python.

# New Methods
----------------------------------------
{{ new_method }}
----------------------------------------"""
