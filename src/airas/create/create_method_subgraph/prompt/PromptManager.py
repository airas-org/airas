
# Separated prompts for each specialized node
# 1. Pure Novelty Verification Prompt (No refinement suggestions)
PURE_NOVELTY_VERIFICATION_PROMPT = """\
# Pure Novelty Assessment Task

You are an expert research evaluator. Your ONLY task is to objectively assess whether the proposed method is genuinely novel. Do NOT provide refinement suggestions or improvements.

## Proposed Method
{{ raw_generated_method }}

## Base Method Used for Creation
{{ base_method_text }}

## Additional Methods Used for Inspiration
{% for add_method_text in add_method_texts %}
---
{{ add_method_text }}
{% endfor %}

## Related Papers from Literature Search
{% for paper in related_papers %}
---
Title: {{ paper.title }}
ArXiv ID: {{ paper.arxiv_id }}
Summary: {{ paper.summary }}
{% endfor %}

## Assessment Instructions

Conduct a thorough, objective evaluation focusing on:

1. **Technical Novelty Analysis**
   - Identify core technical contributions claimed
   - Compare each contribution against existing literature
   - Assess the significance of claimed innovations

2. **Overlap Detection**
   - Identify specific overlaps with related papers
   - Distinguish between minor similarities and major overlaps
   - Highlight truly unique elements (if any)

3. **Scientific Merit Evaluation**
   - Evaluate whether the method advances the field
   - Consider both theoretical and practical contributions
   - Assess the meaningfulness of the combination/approach

## Output Format (JSON only)

```json
{
    "is_novel": true/false,
    "confidence": 0.0-1.0,
    "explanation": "Comprehensive explanation of your assessment with specific references to overlaps and novel elements",
    "specific_issues": ["detailed list of specific novelty issues"],
    "novel_aspects": ["genuinely novel aspects identified, if any"],
    "overlap_analysis": {
        "major_overlaps": ["significant overlaps with specific papers/methods"],
        "minor_similarities": ["minor similarities with existing work"],
        "unique_contributions": ["elements that appear genuinely unique"]
    },
    "significance_level": "high/medium/low"
}
```

**Critical Instructions:**
- Focus SOLELY on assessment - provide NO improvement suggestions
- Be specific about overlaps with citations to related papers
- Base confidence on strength of evidence for/against novelty
- Consider both incremental and breakthrough innovations
"""

# 2. Refinement Feedback Generation Prompt
REFINEMENT_FEEDBACK_PROMPT = """\
# Method Refinement Feedback Generation

You are a research advisor specializing in method improvement. Your task is to provide specific, actionable feedback to enhance the novelty and technical quality of a research method.

## Current Method (Iteration {{ iteration_count }})
{{ current_method }}

## Novelty Assessment Results
- **Is Novel**: {{ is_novel }}
- **Confidence**: {{ confidence }}
- **Main Issues**: {{ specific_issues }}
- **Overlap Analysis**: {{ overlap_analysis }}
- **Detailed Explanation**: {{ explanation }}

## Related Work Context
{% for paper in related_papers %}
- **{{ paper.title }}**: {{ paper.summary.main_contributions }}
{% endfor %}

## Refinement Task

Generate specific, actionable feedback to address the novelty issues identified. Focus on:

### 1. **Specific Problem Areas**
- What exactly lacks novelty or differentiation?
- Which aspects are too similar to existing work?
- Where are the main technical gaps?

### 2. **Differentiation Strategies**
- How to better distinguish from related papers?
- What unique angles or approaches to explore?
- How to emphasize genuinely novel aspects?

### 3. **Technical Enhancement Directions**
- Specific technical improvements to implement
- More sophisticated algorithmic approaches
- Novel architectural or methodological elements

### 4. **Innovation Opportunities**
- Unexplored combinations of techniques
- Emerging trends that could be integrated
- Cross-domain insights to leverage

### 5. **Implementation Sophistication**
- More advanced implementation details
- Technical depth improvements
- Practical innovation opportunities

## Output Format

Provide structured, actionable feedback:

### Immediate Improvements Needed:
- [Specific issue 1 and how to address it]
- [Specific issue 2 and how to address it]
- [Specific issue 3 and how to address it]

### Technical Enhancement Suggestions:
- [Technical improvement 1 with implementation details]
- [Technical improvement 2 with implementation details]
- [Technical improvement 3 with implementation details]

### Differentiation Strategies:
- [Strategy 1 to differentiate from Paper X]
- [Strategy 2 to differentiate from Paper Y]
- [Strategy 3 to emphasize unique aspects]

### Novel Directions to Explore:
- [Direction 1: specific unexplored combination]
- [Direction 2: emerging technique integration]
- [Direction 3: cross-domain innovation]

**Focus on concrete, implementable suggestions that will genuinely improve novelty.**
"""

# 3. Agent Decision Making Prompt
AGENT_DECISION_PROMPT = """\
# Autonomous Agent Decision Making

You are an autonomous research agent responsible for deciding whether to continue refining a method or finalize it.

## Current Situation
- **Iteration**: {{ iteration_count }}/{{ max_iterations }}
- **Method is Novel**: {{ is_novel }}
- **Confidence Score**: {{ confidence }}
- **Novelty Threshold**: {{ novelty_threshold }}

## Verification Results
{{ verification_explanation }}

## Iteration History
{% for iteration in generation_history %}
**Iteration {{ iteration.iteration }}**:
Method: {{ iteration.method[:200] }}...
{% endfor %}

## Previous Feedback Applied
{% for feedback in feedback_history %}
---
{{ feedback }}
{% endfor %}

## Decision Framework

Consider these factors in your decision:

### Hard Constraints
1. If iteration_count >= max_iterations → FINALIZE
2. If is_novel == true AND confidence >= threshold → FINALIZE

### Soft Factors
1. **Improvement Trend**: Are iterations showing meaningful progress?
2. **Diminishing Returns**: Are recent changes making significant improvements?
3. **Technical Quality**: Is the current method technically sound?
4. **Innovation Potential**: Is there clear room for further innovation?
5. **Resource Efficiency**: Is continued iteration worth the computational cost?

### Decision Logic
- **CONTINUE** if: Clear improvement opportunities exist and constraints allow
- **FINALIZE** if: Method is sufficiently novel OR max iterations reached OR diminishing returns evident

## Required Output (JSON)

```json
{
    "decision": "continue" or "finalize",
    "reasoning": "Detailed explanation of your decision based on the factors above",
    "confidence_in_decision": 0.0-1.0,
    "key_factors": ["list of main factors that influenced the decision"],
    "expected_improvement_potential": "high/medium/low (if continuing)"
}
```

**Make a clear, justified decision based on objective analysis of progress and constraints.**
"""

# 4. Enhanced Generator Prompt with Refinement Context
ENHANCED_GENERATOR_PROMPT = """\
# Method Generation/Refinement Task

{% if is_refinement %}
## Refinement Mode (Iteration {{ iteration_count }})

You are refining a method based on specific feedback. Create a significantly improved version that addresses all identified issues.

### Previous Method
{{ previous_method }}

### Specific Refinement Feedback
{{ refinement_feedback }}

### Instructions
Create a substantially improved method that:
1. **Addresses every point** in the refinement feedback
2. **Incorporates suggested technical enhancements**
3. **Differentiates clearly** from identified overlapping work
4. **Introduces more sophisticated** technical elements
5. **Maintains coherence** while adding innovation

{% else %}
## Initial Generation Mode

You are creating a novel method by combining and extending existing approaches.

### Base Method
{{ base_method_text }}

### Additional Methods for Inspiration
{% for add_method in add_method_texts %}
---
{{ add_method }}
{% endfor %}

### Instructions
Create a novel method that:
1. **Builds upon the base method** as foundation
2. **Incorporates innovative elements** from additional methods
3. **Introduces genuinely novel combinations**
4. **Addresses limitations** of existing approaches
5. **Provides clear technical advantages**

{% endif %}

## Output Requirements

Provide a comprehensive method description including:

### Method Overview
- High-level description of the approach
- Key innovations and differentiators
- Target problem and application domain

### Technical Details
- Detailed algorithmic/procedural steps
- Mathematical formulations (if applicable)
- Architectural specifications
- Parameter considerations

### Novel Contributions
- Specific innovations introduced
- How they differ from existing work
- Technical advantages provided

### Implementation Framework
- Practical implementation considerations
- Computational requirements
- Integration guidelines
- Performance expectations

**Focus on creating a technically sophisticated, genuinely innovative method.**
"""


class PromptManager:
    """Centralized prompt management for the separated node architecture"""

    @staticmethod
    def get_novelty_verification_prompt():
        return PURE_NOVELTY_VERIFICATION_PROMPT

    @staticmethod
    def get_refinement_feedback_prompt():
        return REFINEMENT_FEEDBACK_PROMPT

    @staticmethod
    def get_agent_decision_prompt():
        return AGENT_DECISION_PROMPT

    @staticmethod
    def get_generator_prompt():
        return ENHANCED_GENERATOR_PROMPT

    @staticmethod
    def render_prompt(template_str: str, **kwargs):
        """Render a Jinja2 template with provided context"""
        from jinja2 import Environment
        env = Environment()
        template = env.from_string(template_str)
        return template.render(**kwargs)

