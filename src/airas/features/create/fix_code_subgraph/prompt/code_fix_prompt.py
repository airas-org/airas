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
   - **Data pipeline fixes**: Ensure complete data acquisition (download, extract, organize into data/)
   - **Dependency resolution fixes**: Check requirements.txt for circular dependencies and proper ordering
   - **Fail-fast, no silent fallbacks**: If real datasets or models cannot be accessed, terminate execution immediately with clear error messages rather than using synthetic alternatives.

# Rules
- Fix all errors found in the error messages
- If a file has no errors, return exactly: `[KEEP_ORIGINAL_FILE]`
- Only reference files that exist in the "Current Files" section - do not import or reference non-existent files
- Ensure code runs on NVIDIA Tesla T4 · 16 GB VRAM
- Update requirements.txt if new packages needed
- Save all experiment images to: .research/iteration{{ experiment_iteration }}/images (modify any existing image save paths to use this exact directory)

# ========================================
# ERROR INFORMATION TO FIX
# ========================================

## Output Data:
{{ new_method.experimental_results.result }}

## Error Data:
{{ new_method.experimental_results.error }}

# ========================================
# CURRENT FILES TO FIX
# ========================================
The following files contain errors and need to be fixed:
{% for file_path, content in current_files.items() %}
## {{ file_path }}
```python
{{ content }}
```

{% endfor %}"""
