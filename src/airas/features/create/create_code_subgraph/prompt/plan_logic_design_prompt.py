plan_logic_design_prompt = """\
You are an expert dependency analyst for software projects.

Your sole task is to determine the optimal, sequential order for generating a set of source code files based on their internal dependencies. An incorrect order will lead to compilation or import errors.

# Input 1: Original Research Context
- Method: {{ new_method.method }}
- Experimental Strategy: {{ new_method.experimental_design.experiment_strategy }}
- Experimental Details: {{ new_method.experimental_design.experiment_details }}
{% if new_method.experimental_design.external_resources %}
- External Resources: {{ new_method.experimental_design.external_resources }}
{% endif %}

# Input 2: Architecture Design
You are given the following software architecture design, which defines the core components (files) and their relationships.

{{ architecture_design }}

# Instructions
1.  **Analyze Dependencies**: Carefully review the `internal_dependencies` of each component in the `core_components` list. A component can only be generated *after* all of its dependencies have been generated.
2.  **Determine Generation Order**: Based on the dependency analysis, create a single, ordered list of file paths for generation. This is a topological sort of the dependency graph. Start with components that have no dependencies and move to components that depend on them.
3.  **Handle Tasks (Optional)**: You can optionally create a high-level task breakdown that maps to the generation order, but the `generation_order` list is the primary output.

"""
