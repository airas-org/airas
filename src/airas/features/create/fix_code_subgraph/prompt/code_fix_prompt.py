code_fix_prompt = """\
# Instructions
You are tasked with fixing Python code that failed during execution. Analyze the error messages and output data to identify and fix the issues in the provided files.

# Problem-Solving Approach
1. **Root Cause Analysis**: Identify the underlying cause, not just the symptom
   - Trace error messages to their source in the code
   - Understand the context and expected behavior
   - Consider data flow and dependencies

2. **Systematic Debugging**:
   - Import/Environment: Library availability, versions, installation
   - Data Type/Shape: Input/output formats, dimensions, type compatibility
   - Logic/Algorithm: Algorithmic assumptions and edge cases
   - Resource: Memory, compute, hardware constraints

3. **Solution Strategy**:
   - Apply minimal, targeted fixes rather than wholesale rewrites
   - Consider alternative approaches if original method is flawed
   - Fail-fast policy: All error handling must result in immediate program termination with clear error messages. No silent fallbacks or synthetic alternatives
   - Data pipeline fixes: Ensure complete data acquisition (download, extract, organize into data/)
   - Dependency resolution fixes: Check pyproject.toml for circular dependencies and proper ordering
{% if secret_names %}
   - Environment Variables: The following environment variables are available for use: {{ secret_names|join(', ') }}. Use os.getenv() to access them in your code for authentication tokens and API keys.
{% endif %}

# Rules
- Fix all errors found in the error messages
- Proactive Error Detection: Beyond fixing reported errors, use the Systematic Debugging approach above to inspect code for potential issues
- If the Output Data lacks concrete experimental results (only contains logs without actual numerical data, metrics, or experimental findings), this must be treated as an error and fixed.
  - When this happens, it is absolutely not acceptable to leave the code unmodified, as the lack of clear results indicates a failure in the experiment itself.
- If similar errors appear in the Previous Error History, consider alternative approaches rather than repeating the same fixes
- If a file has no errors AND contains concrete experimental data in the output, return exactly: `[KEEP_ORIGINAL_FILE]`
- Only reference files that exist in the "CURRENT FILES" section - do not import or reference non-existent files
- Update pyproject.toml if new packages needed
- Do not shorten or omit any code. Always provide the full and complete code for each file.
- MANDATORY: You must update paths before saving. The following paths are required:
- Image paths: .research/iteration{{ experiment_iteration }}/images (modify any existing image save paths to use this exact directory)
- JSON paths: .research/iteration{{ experiment_iteration }}/ (Save each experiment's results as separate JSON files in this directory and print each JSON contents to standard output for verification)

# Configuration Files Requirements
- Generate TWO separate configuration files:
  - config/smoke_test.yaml: Small-scale configuration for quick validation (reduced epochs like 1-2, smaller datasets, limited iterations)
  - config/full_experiment.yaml: Full-scale configuration for complete experimental runs
- Ensure main.py supports command-line arguments:
  - --smoke-test flag: loads smoke_test.yaml
  - --full-experiment flag: loads full_experiment.yaml
- Use PyYAML for configuration loading in main.py


# ========================================
# ERROR INFORMATION TO FIX
# ========================================

- Output Data: {{ new_method.experimental_results.result }}
- Error Data: {{ new_method.experimental_results.error }}

# ========================================
# CURRENT FILES TO FIX
# ========================================
The following files contain issues and need to be fixed:
{{ new_method.experimental_design.experiment_code | tojson }}

{% if file_static_validations %}
# ========================================
# STATIC VALIDATION RESULTS - FIX THESE ISSUES
# ========================================
Focus on fixing the static validation issues below. Ignore any previous execution errors as these validation results are more current and relevant.

## All Static Validation Issues:
{% for file_path, file_static_validation in file_static_validations.items() %}
{% if file_static_validation.errors %}
### Errors in {{ file_path }}:
{% for error in file_static_validation.errors %}
- {{ error }}
{% endfor %}
{% endif %}

{% if file_static_validation.warnings %}
### Warnings in {{ file_path }}:
{% for warning in file_static_validation.warnings %}
- {{ warning }}
{% endfor %}
{% endif %}
{% endfor %}
{% endif %}

# ========================================
# EXPERIMENTAL CONTEXT
# ========================================
# The following experimental context is provided to prevent the solution from diverging in the wrong direction during fix iterations.

# Current Research Method (Target for Experiment Design)
{{ new_method.method }}

# Experimental Design
- Strategy: {{ new_method.experimental_design.experiment_strategy }}
- Details: {{ new_method.experimental_design.experiment_details }}

## External Resources (for reference):
{{ new_method.experimental_design.external_resources }}

# ========================================
# Previous Error History (for reference - avoid repeating same fixes)
# ========================================
{% if error_list %}
{% for error in error_list %}
### {{ loop.index }}. {{ error }}
{% endfor %}
{% endif %}"""
