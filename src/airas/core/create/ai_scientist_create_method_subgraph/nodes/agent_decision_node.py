import json
from logging import getLogger
from typing import Any, Dict

from airas.create.create_method_subgraph.create_method_subgraphv2 import (
    CreateMethodSubgraphState,
)
from airas.create.create_method_subgraph.prompt.PromptManager import PromptManager

logger = getLogger(__name__)


def agent_decision_node(
    self,
    state: CreateMethodSubgraphState,
    verification_result: Dict[str, Any],
    iteration_count: int,
    max_iterations: int,
    confidence_score: float,
) -> str:
    """Agent decides whether to continue or finalize based on multiple factors"""

    # Hard constraints
    if iteration_count >= max_iterations:
        print(f"🛑 HARD CONSTRAINT: Max iterations ({max_iterations}) reached")
        return "finalize"

    if (
        verification_result.get("is_novel", False)
        and confidence_score >= self.novelty_threshold
    ):
        print(
            f"✅ HARD CONSTRAINT: Novel method with high confidence ({confidence_score:.2f} >= {self.novelty_threshold})"
        )
        return "finalize"

    # Use the predefined AGENT_DECISION_PROMPT
    print("🧠 Using predefined AGENT_DECISION_PROMPT for decision making...")

    try:
        # Prepare the data for the template
        template_data = {
            "iteration_count": iteration_count,
            "max_iterations": max_iterations,
            "is_novel": verification_result.get("is_novel", False),
            "confidence": confidence_score,
            "novelty_threshold": self.novelty_threshold,
            "verification_explanation": verification_result.get("explanation", ""),
            "generation_history": state.get("generation_history", []),
            "feedback_history": state.get("feedback_history", []),
        }

        # Render the prompt using PromptManager
        agent_prompt = PromptManager.render_prompt(
            PromptManager.get_agent_decision_prompt, **template_data
        )

        print("📝 Rendered agent decision prompt successfully")

        response, _ = self.client.generate(message=agent_prompt)
        decision_data = json.loads(response)

        reasoning = decision_data.get("reasoning", "")
        decision = decision_data.get("decision", "finalize")
        key_factors = decision_data.get("key_factors", [])
        confidence_in_decision = decision_data.get("confidence_in_decision", 0.5)

        print(f"🤔 Agent reasoning: {reasoning[:150]}...")
        print(
            f"🔑 Key factors: {', '.join(key_factors[:3])}..."
        )  # Show first 3 factors
        print(f"🎯 Decision confidence: {confidence_in_decision:.2f}")

        logger.info(f"Agent reasoning: {reasoning}")
        return decision

    except Exception as e:
        print(f"⚠️ Error in agent decision making: {e}")
        logger.warning(f"Error in agent decision making: {e}")
        # Fallback logic
        if verification_result.get("is_novel", False):
            print("🔄 Fallback: Novel method detected, finalizing")
            return "finalize"
        elif iteration_count < max_iterations - 1:
            print("🔄 Fallback: Continuing iteration")
            return "continue"
        else:
            print("🔄 Fallback: Near max iterations, finalizing")
            return "finalize"
