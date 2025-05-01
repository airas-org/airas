generator_node_prompt = """\
Your task is to propose a genuinely novel method that mitigates one or more challenges in the “Base Method.” This must go beyond a mere partial modification of the Base Method. To achieve this, reason through the following steps and provide the outcome of step 3:
- Identify multiple potential issues with the “Base Method.”
- From the “Add Method” approaches, select one that can address at least one of the issues identified in step 1.
- Drawing inspiration from both the “Base Method” and the selected approach in step 2, devise a truly new method.

# Base Method
{{ base_method_text }}

# Add Method
{{ add_method_text }}"""
