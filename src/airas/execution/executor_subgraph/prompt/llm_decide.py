llm_decide_prompt = """\
# Instructions:
You determine whether the Python script has succeeded or failed based on the given information. You must output True or False according to the following rules.

# Rules:
- Output False if “Error Data” contains an error. If “Error Date” contains a non-error or empty content, output True.
- Output False if both “Error Data” and “Output Data” are empty.

# Error Data:
{{ error_text_data }}
# Output Data:
{{ output_text_data }}"""
