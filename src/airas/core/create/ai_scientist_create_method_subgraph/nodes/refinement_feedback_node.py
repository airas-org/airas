from logging import getLogger
from typing import Any, Dict

from airas.create.create_method_subgraph.prompt.PromptManager import PromptManager

logger = getLogger(__name__)


def refinement_feedback_node(
    self, verification_result: Dict[str, Any], current_method: str, iteration_count: int
) -> str:
    """Generate specific, actionable feedback for method refinement using predefined prompt"""

    is_novel = verification_result.get("is_novel", False)
    confidence = verification_result.get("confidence", 0.0)

    if is_novel:
        print(
            "📝 Generating improvement feedback for novel method (confidence enhancement)..."
        )
    else:
        print("📝 Generating refinement feedback for non-novel method...")

    try:
        # Get related papers from verification result
        related_papers = verification_result.get("related_papers", [])

        # Prepare template data
        template_data = {
            "iteration_count": iteration_count,
            "current_method": current_method,
            "is_novel": is_novel,
            "confidence": confidence,
            "specific_issues": verification_result.get("specific_issues", []),
            "overlap_analysis": verification_result.get("overlap_analysis", {}),
            "explanation": verification_result.get("explanation", ""),
            "related_papers": related_papers,
        }

        # For novel methods, modify the prompt to focus on confidence improvement
        if is_novel and confidence < 1.0:
            print(f"🎯 Focusing on confidence improvement (current: {confidence:.2f})")

            # Create a modified prompt for novel methods that need confidence improvement
            confidence_improvement_context = f"""
NOTE: This method has been assessed as NOVEL (confidence: {confidence:.2f}), but there is room for improvement to increase confidence and robustness. Focus your feedback on:

1. **Confidence Enhancement**: How to strengthen the novel aspects to increase assessment confidence
2. **Technical Robustness**: Ways to make the novel contributions more technically sound
3. **Clearer Differentiation**: Better articulation of what makes this method unique
4. **Implementation Sophistication**: More advanced technical details to strengthen the approach
5. **Broader Impact**: Expanding the scope or applicability of the novel approach

Your feedback should help elevate this already novel method to be even more compelling and technically robust.
"""

            # Add this context to the template data
            template_data["explanation"] = (
                confidence_improvement_context
                + "\n\nOriginal Assessment: "
                + template_data["explanation"]
            )

        # Render the prompt using PromptManager
        feedback_prompt = PromptManager.render_prompt(
            PromptManager.get_refinement_feedback_prompt, **template_data
        )

        print("✅ Rendered refinement feedback prompt successfully")

        # Generate feedback using LLM
        feedback, _ = self.client.generate(message=feedback_prompt)

        print(f"📋 Generated feedback length: {len(feedback)} characters")
        return feedback

    except Exception as e:
        print(f"❌ Error generating refinement feedback: {e}")
        logger.warning(f"Error generating refinement feedback: {e}")

        # Enhanced fallback feedback based on novelty status
        if is_novel:
            explanation = verification_result.get("explanation", "")
            return f"""
### Confidence Enhancement Needed:
- Method shows novelty (confidence: {confidence:.2f}) but can be strengthened further
- Need to better articulate unique technical contributions
- Enhance implementation details for greater robustness

### Technical Enhancement Suggestions:
- Provide more sophisticated algorithmic descriptions
- Add mathematical formulations where applicable
- Include detailed architectural specifications
- Strengthen theoretical foundations

### Differentiation Strategies:
- More clearly highlight what distinguishes this from existing approaches
- Emphasize unique technical advantages
- Better explain the innovative combinations used

### Novel Directions to Explore:
- Expand the scope of the novel approach
- Consider additional applications or domains
- Integrate with emerging trends in the field
- Explore cross-domain innovations

Assessment details: {explanation}
"""
        else:
            explanation = verification_result.get("explanation", "")
            return f"""
### Immediate Improvements Needed:
- Method lacks sufficient novelty based on assessment
- Need to address overlaps with existing work
- Technical contributions require strengthening

### Technical Enhancement Suggestions:
- Introduce more sophisticated algorithmic approaches
- Add novel architectural elements
- Implement advanced technical features

### Differentiation Strategies:
- Better distinguish from existing methods in literature
- Emphasize unique technical aspects
- Address specific limitations identified in assessment

### Novel Directions to Explore:
- Explore unexplored combinations of techniques
- Integrate emerging trends in the field
- Consider cross-domain innovations

Issues identified: {explanation}
Consider adding more innovative technical elements and better differentiation from existing approaches.
"""
