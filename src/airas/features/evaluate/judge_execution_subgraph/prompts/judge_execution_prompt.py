judge_execution_prompt = """\
# Instructions:
You determine whether the Python script has succeeded or failed based on the given information.
Output True if the script SUCCEEDED, False if it FAILED.
Follow the rules below:

# Rules:
- Output False if "Error Data" contains any error messages or exceptions.
- Output False if both "Error Data" and "Output Data" are empty.
- Output False if "Output Data" does not contain clear experimental results such as:
  - Quantitative results or measurements
  - Numerical comparisons or improvements
  - Completion messages indicating successful execution
  - Statistical analysis or evaluation results
- Output True ONLY if "Output Data" contains clear evidence of successful experimental execution with meaningful results.

# Error Data:
{{ error_text_data }}
# Output Data:
{{ output_text_data }}"""
