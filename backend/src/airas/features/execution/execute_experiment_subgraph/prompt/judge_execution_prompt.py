judge_execution_prompt = """\
# Instructions:
You determine whether the Python script has succeeded or failed based on the given information.
Output True if the script SUCCEEDED, False if it FAILED.
Follow the rules below:

# Rules:
- Output False if "Standard Error" contains actual error messages, exceptions, or tracebacks (e.g., "Error", "Exception", "Traceback").
- Ignore warnings (e.g., DeprecationWarning, FutureWarning, UserWarning) - they should NOT cause a failure.
- Output True if the script completed without errors and "Standard Output" shows evidence of successful execution, such as:
  - Completion messages indicating the script finished normally
  - Progress logs showing the script ran through its stages
  - Any output indicating normal termination (even if minimal in trial mode)
- The script may be running in trial mode (lightweight validation), so minimal output is acceptable as long as there are no errors.

# Standard Error:
{{ stderr_text }}
# Standard Output:
{{ stdout_text }}"""
