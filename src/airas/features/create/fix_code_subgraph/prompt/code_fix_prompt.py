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
   - Use defensive programming (bounds checking, error handling)
   - Consider alternative approaches if original method is flawed
   - Preserve intended functionality and backward compatibility
   - Data pipeline fixes: Ensure complete data acquisition (download, extract, organize into data/)
   - Dependency resolution fixes: Check pyproject.toml for circular dependencies and proper ordering.
   - Fail-fast, no silent fallbacks: If real datasets or models cannot be accessed, terminate execution immediately with clear error messages rather than using synthetic alternatives.

# Rules
- Fix all errors found in the error messages
- If the Output Data lacks concrete experimental results (only contains logs without actual numerical data, metrics, or experimental findings), this must be treated as an error and fixed
- If similar errors appear in the Previous Error History, consider alternative approaches rather than repeating the same fixes
- If a file has no errors AND contains concrete experimental data in the output, return exactly: `[KEEP_ORIGINAL_FILE]`
- Only reference files that exist in the "CURRENT FILES" section - do not import or reference non-existent files
- Ensure code runs on NVIDIA Tesla T4 · 16 GB VRAM
- Update pyproject.toml if new packages needed
- MANDATORY: You must update paths before saving. The following paths are required:
- Image paths: .research/iteration{{ experiment_iteration }}/images (modify any existing image save paths to use this exact directory)
- JSON paths: .research/iteration{{ experiment_iteration }}/ (Save each experiment's results as separate JSON files in this directory and print each JSON contents to standard output for verification)

# ========================================
# ERROR INFORMATION TO FIX
# ========================================

## Output Data:
{{ new_method.experimental_results.result }}

## Error Data:
{{ new_method.experimental_results.error }}

## External Resources (for reference):
{{ new_method.experimental_design.external_resources }}

# ========================================
# CURRENT FILES TO FIX
# ========================================
The following files contain errors and need to be fixed:
{% for file_path, content in generated_file_contents.items() %}
## {{ file_path }}
```python
{{ content }}
```
{% endfor %}

# ========================================
# COMMON ERROR PATTERNS & SOLUTIONS
# ========================================
- ModuleNotFoundError Fix: If encountering `No module named 'src.xyz'`, consolidate missing functionality into existing files rather than assuming external modules exist

# ========================================
# Previous Error History (for reference - avoid repeating same fixes)
# ========================================
{% if error_list %}
{% for error in error_list %}
### {{ loop.index }}. {{ error }}
{% endfor %}
{% endif %}
"""
