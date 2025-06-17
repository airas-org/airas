import argparse
import json
import logging
from typing import Any, Dict, List, TypeVar

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.core.create.ai_scientist_create_method_subgraph.nodes.generator_node import generator_node
from airas.core.create.ai_scientist_create_method_subgraph.nodes.agent_decision_node import agent_decision_node
from airas.core.create.ai_scientist_create_method_subgraph.nodes.refinement_feedback_node import refinement_feedback_node
from airas.core.create.ai_scientist_create_method_subgraph.prompt.PromptManager import PromptManager
from airas.core.create.ai_scientist_create_method_subgraph.nodes.pure_novelty_verification_node import pure_novelty_verification_node
from airas.types.paper import CandidatePaperInfo
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL, LLMFacadeClient
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

class CreateMethodSubgraphInputState(TypedDict):
    base_method_text: CandidatePaperInfo
    add_method_texts: list[CandidatePaperInfo]


class CreateMethodSubgraphHiddenState(TypedDict):
    raw_generated_method: str
    verification_result: Dict[str, Any]
    iteration_count: int
    generation_history: List[Dict[str, Any]]
    feedback_history: List[str]
    max_iterations: int
    agent_decision: str
    confidence_score: float
    refinement_feedback: str


class CreateMethodSubgraphOutputState(TypedDict):
    new_method: str
    final_verification_result: Dict[str, Any]
    total_iterations: int


class CreateMethodSubgraphState(
    CreateMethodSubgraphInputState,
    CreateMethodSubgraphHiddenState,
    CreateMethodSubgraphOutputState,
    ExecutionTimeState,
):
    pass


T = TypeVar("T")


def print_node_start(node_name: str, iteration: int = None):
    """Print node execution start with visual formatting"""
    if iteration is not None:
        print(f"\n{'='*60}")
        print(f"🚀 STARTING NODE: {node_name} (Iteration {iteration})")
        print(f"{'='*60}")
    else:
        print(f"\n{'='*60}")
        print(f"🚀 STARTING NODE: {node_name}")
        print(f"{'='*60}")


def print_node_end(node_name: str, result_summary: str = ""):
    """Print node execution end with result summary"""
    print(f"✅ COMPLETED NODE: {node_name}")
    if result_summary:
        print(f"📋 RESULT: {result_summary}")
    print(f"{'='*60}\n")


def print_routing_decision(from_node: str, to_node: str, reason: str = ""):
    """Print routing decision between nodes"""
    print(f"\n🔀 ROUTING: {from_node} → {to_node}")
    if reason:
        print(f"📝 REASON: {reason}")
    print("-" * 40)


class AIScientistCreateMethodSubgraph:
    def __init__(
        self,
        llm_name: LLM_MODEL,
        num_retrieve_paper: int,
        max_iterations: int = 5,
        novelty_threshold: float = 0.7,
    ):
        self.llm_name = llm_name
        self.num_retrieve_paper = num_retrieve_paper
        self.max_iterations = max_iterations
        self.novelty_threshold = novelty_threshold
        self.client = LLMFacadeClient(llm_name=llm_name)
        check_api_key(llm_api_key_check=True)

        print(f"\n🔧 INITIALIZED CreateMethodSubgraph:")
        print(f"   LLM: {llm_name}")
        print(f"   Max Iterations: {max_iterations}")
        print(f"   Novelty Threshold: {novelty_threshold}")
        print(f"   Papers to Retrieve: {num_retrieve_paper}")

    @time_node("create_method_subgraph", "_initialization_node")
    def _initialization_node(self, state: CreateMethodSubgraphState) -> dict:
        """Initialize the iterative process"""
        print_node_start("INITIALIZATION")
        logger.info("---CreateMethodSubgraph Initialization Node---")

        result = {
            "iteration_count": 0,
            "generation_history": [],
            "feedback_history": [],
            "max_iterations": self.max_iterations,
            "confidence_score": 0.0,
            "refinement_feedback": ""
        }

        print(f"📊 Initial State Set:")
        print(f"   Max Iterations: {self.max_iterations}")
        print(f"   Starting Iteration Count: 0")

        print_node_end("INITIALIZATION", "Process initialized successfully")
        return result

    @time_node("create_method_subgraph", "_generator_node")
    def _generator_node(self, state: CreateMethodSubgraphState) -> dict:
        """Generate or refine method based on feedback"""
        current_iteration = state.get('iteration_count', 0) + 1
        print_node_start("GENERATOR", current_iteration)
        logger.info(f"---CreateMethodSubgraph Generator Node (Iteration {current_iteration})---")

        # Check if this is a refinement iteration
        is_refinement = state.get("iteration_count", 0) > 0 and state.get("refinement_feedback")

        print(f"🔍 Generation Mode: {'REFINEMENT' if is_refinement else 'INITIAL'}")

        if is_refinement:
            print("📝 Using ENHANCED_GENERATOR_PROMPT for refinement...")

            # Use ENHANCED_GENERATOR_PROMPT for refinement
            try:
                # Prepare template data for refinement
                template_data = {
                    "is_refinement": True,
                    "iteration_count": current_iteration,
                    "previous_method": state.get("raw_generated_method", ""),
                    "refinement_feedback": state.get("refinement_feedback", ""),
                    "base_method_text": state["base_method_text"],
                    "add_method_texts": state["add_method_texts"]
                }

                # Render the enhanced generator prompt
                enhanced_prompt = PromptManager.render_prompt(
                    PromptManager.get_generator_prompt,
                    **template_data
                )

                print("✅ Rendered ENHANCED_GENERATOR_PROMPT for refinement")

                # Generate using LLM directly instead of generator_node
                new_method, _ = self.client.generate(message=enhanced_prompt)

                print(f"🔧 Generated refined method using enhanced prompt")

            except Exception as e:
                print(f"⚠️ Error with enhanced generator prompt: {e}")
                print("🔄 Falling back to enhanced context method...")

                # Fallback: Create enhanced context for original generator_node
                enhanced_base_method = f"""
ORIGINAL BASE METHOD:
{state["base_method_text"]}

PREVIOUS ITERATION (Iteration {current_iteration - 1}):
{state.get("raw_generated_method", "")}

REFINEMENT FEEDBACK TO ADDRESS:
{state.get("refinement_feedback", "")}

VERIFICATION RESULTS FROM PREVIOUS ITERATION:
- Novel: {state.get("verification_result", {}).get("is_novel", "Unknown")}
- Confidence: {state.get("verification_result", {}).get("confidence", "Unknown")}
- Issues: {state.get("verification_result", {}).get("specific_issues", [])}
- Explanation: {state.get("verification_result", {}).get("explanation", "")}

GENERATION HISTORY:
{json.dumps(state.get("generation_history", []), indent=2)}

TASK: Create a significantly improved method that addresses all the feedback above while building upon the original base method. Focus on:
1. Addressing every point in the refinement feedback
2. Incorporating suggested technical enhancements
3. Differentiating clearly from identified overlapping work
4. Introducing more sophisticated technical elements
5. Maintaining coherence while adding innovation
"""

                # Call generator_node with enhanced context as base_method_text
                new_method = generator_node(
                    llm_name=self.llm_name,
                    base_method_text=enhanced_base_method,
                    add_method_texts=state["add_method_texts"]
                )
        else:
            print("🆕 Generating initial method from base and additional methods...")

            # Use ENHANCED_GENERATOR_PROMPT for initial generation too
            try:
                # Prepare template data for initial generation
                template_data = {
                    "is_refinement": False,
                    "base_method_text": state["base_method_text"],
                    "add_method_texts": state["add_method_texts"]
                }

                # Render the enhanced generator prompt
                enhanced_prompt = PromptManager.render_prompt(
                    PromptManager.get_generator_prompt,
                    **template_data
                )

                print("✅ Rendered ENHANCED_GENERATOR_PROMPT for initial generation")

                # Generate using LLM directly
                new_method, _ = self.client.generate(message=enhanced_prompt)

                print(f"🔧 Generated initial method using enhanced prompt")

            except Exception as e:
                print(f"⚠️ Error with enhanced generator prompt: {e}")
                print("🔄 Falling back to original generator_node...")

                # Fallback to original generator_node
                new_method = generator_node(
                    llm_name=self.llm_name,
                    base_method_text=state["base_method_text"],
                    add_method_texts=state["add_method_texts"]
                )

        # Update generation history with more detailed information
        generation_history = state.get("generation_history", [])

        # Preserve verification results and feedback from previous iteration
        previous_verification = None
        previous_feedback = None
        if generation_history:
            last_entry = generation_history[-1]
            previous_verification = last_entry.get("verification_result")
            previous_feedback = last_entry.get("refinement_feedback")

        new_entry = {
            "iteration": current_iteration,
            "method": new_method,
            "is_refinement": is_refinement,
            "timestamp": "2025-01-31",
            "previous_verification_result": state.get("verification_result") if is_refinement else None,
            "applied_feedback": state.get("refinement_feedback") if is_refinement else None,
            "base_method_preserved": True
        }

        generation_history.append(new_entry)

        # 🆕 DETAILED OUTPUT: Show generated method content
        print(f"\n{'='*80}")
        print(f"📝 GENERATED METHOD (Iteration {current_iteration}):")
        print(f"{'='*80}")
        print(new_method)
        print(f"{'='*80}\n")

        print(f"✨ Generated method preview (first 200 chars):")
        print(f"   {new_method[:200]}...")
        print(f"📈 Total generation attempts: {len(generation_history)}")
        print(f"📊 Method length: {len(new_method)} characters")

        if is_refinement:
            print(f"🔄 Applied refinement feedback from previous iteration")
            print(f"📊 Previous verification: Novel={state.get('verification_result', {}).get('is_novel', 'Unknown')}")

            # Show what feedback was applied
            feedback = state.get("refinement_feedback", "")
            if feedback:
                print(f"\n📝 APPLIED REFINEMENT FEEDBACK:")
                print(f"{'='*50}")
                print(feedback[:500] + "..." if len(feedback) > 500 else feedback)
                print(f"{'='*50}\n")

        logger.info(f"Generated method (iteration {current_iteration}): {new_method[:200]}...")

        result = {
            "raw_generated_method": new_method,
            "generation_history": generation_history,
            "iteration_count": current_iteration
        }

        print_node_end("GENERATOR", f"Method generated for iteration {current_iteration}")
        return result

    @time_node("create_method_subgraph", "_novelty_verification_node")
    def _novelty_verification_node(self, state: CreateMethodSubgraphState) -> dict:
        """Pure novelty verification without refinement"""
        print_node_start("NOVELTY_VERIFICATION")
        logger.info("---CreateMethodSubgraph Novelty Verification Node---")

        print("🔬 Starting novelty verification process...")
        print(f"📚 Will retrieve up to {self.num_retrieve_paper} related papers")

        verification_result = pure_novelty_verification_node(
            llm_name=self.llm_name,
            raw_generated_method=state["raw_generated_method"],
            base_method_text=state["base_method_text"],
            add_method_texts=state["add_method_texts"],
            num_retrieve_paper=self.num_retrieve_paper
        )

        # Print verification results
        is_novel = verification_result.get("is_novel", False)
        confidence = verification_result.get("confidence", 0.0)
        explanation = verification_result.get("explanation", "")
        specific_issues = verification_result.get("specific_issues", [])
        novel_aspects = verification_result.get("novel_aspects", [])
        overlap_analysis = verification_result.get("overlap_analysis", {})
        significance_level = verification_result.get("significance_level", "medium")
        related_papers = verification_result.get("related_papers", [])

        print(f"📊 VERIFICATION RESULTS:")
        print(f"   Novel: {'✅ YES' if is_novel else '❌ NO'}")
        print(f"   Confidence: {confidence:.2f}")
        print(f"   Significance Level: {significance_level}")
        print(f"   Issues Count: {len(specific_issues)}")
        print(f"   Novel Aspects: {len(novel_aspects)}")
        print(f"   Related Papers Analyzed: {len(related_papers)}")

        # 🆕 DETAILED OUTPUT: Show verification details
        print(f"\n{'='*80}")
        print(f"🔍 DETAILED VERIFICATION RESULTS:")
        print(f"{'='*80}")

        print(f"📝 EXPLANATION:")
        print(explanation)
        print()

        if specific_issues:
            print(f"⚠️ SPECIFIC ISSUES ({len(specific_issues)}):")
            for i, issue in enumerate(specific_issues, 1):
                print(f"   {i}. {issue}")
            print()

        if novel_aspects:
            print(f"✨ NOVEL ASPECTS ({len(novel_aspects)}):")
            for i, aspect in enumerate(novel_aspects, 1):
                print(f"   {i}. {aspect}")
            print()

        if overlap_analysis:
            print(f"🔄 OVERLAP ANALYSIS:")
            major_overlaps = overlap_analysis.get("major_overlaps", [])
            minor_similarities = overlap_analysis.get("minor_similarities", [])
            unique_contributions = overlap_analysis.get("unique_contributions", [])

            if major_overlaps:
                print(f"   🚨 Major Overlaps ({len(major_overlaps)}):")
                for overlap in major_overlaps:
                    print(f"      • {overlap}")

            if minor_similarities:
                print(f"   📝 Minor Similarities ({len(minor_similarities)}):")
                for similarity in minor_similarities:
                    print(f"      • {similarity}")

            if unique_contributions:
                print(f"   ⭐ Unique Contributions ({len(unique_contributions)}):")
                for contribution in unique_contributions:
                    print(f"      • {contribution}")
            print()

        if related_papers:
            print(f"📚 RELATED PAPERS ANALYZED ({len(related_papers)}):")
            for i, paper in enumerate(related_papers[:3], 1):  # Show top 3
                title = paper.get("title", "Unknown")
                arxiv_id = paper.get("arxiv_id", "Unknown")
                print(f"   {i}. {title} (arXiv:{arxiv_id})")
            if len(related_papers) > 3:
                print(f"   ... and {len(related_papers) - 3} more papers")
            print()

        print(f"{'='*80}\n")

        logger.info(f"Verification result: {verification_result}")

        result = {"verification_result": verification_result}
        print_node_end("NOVELTY_VERIFICATION", f"Novel: {is_novel}, Confidence: {confidence:.2f}, Significance: {significance_level}")
        return result

    @time_node("create_method_subgraph", "_agent_decision_node")
    def _agent_decision_node(self, state: CreateMethodSubgraphState) -> Dict[str, Any]:
        """Agent decides whether to continue iterating or finalize"""
        print_node_start("AGENT_DECISION")
        logger.info("---CreateMethodSubgraph Agent Decision Node---")

        verification_result = state["verification_result"]
        iteration_count = state.get("iteration_count", 0)
        max_iterations = state.get("max_iterations", self.max_iterations)

        # Calculate confidence score based on verification result
        confidence_score = self._calculate_confidence_score(verification_result)

        print(f"🤖 AGENT ANALYSIS:")
        print(f"   Current Iteration: {iteration_count}/{max_iterations}")
        print(f"   Method is Novel: {verification_result.get('is_novel', False)}")
        print(f"   Confidence Score: {confidence_score:.2f}")
        print(f"   Novelty Threshold: {self.novelty_threshold}")

        # Agent makes decision
        print("🔄 Agent making decision...")
        agent_decision = agent_decision_node(
            state=state,  # Pass the entire state object
            verification_result=verification_result,
            iteration_count=iteration_count,
            max_iterations=max_iterations,
            confidence_score=confidence_score
        )

        print(f"🎯 AGENT DECISION: {agent_decision.upper()}")

        # 🆕 DETAILED OUTPUT: Show agent decision analysis
        print(f"\n{'='*80}")
        print(f"🤖 AGENT DECISION ANALYSIS:")
        print(f"{'='*80}")

        print(f"📊 DECISION FACTORS:")
        print(f"   • Iteration Progress: {iteration_count}/{max_iterations} ({(iteration_count/max_iterations)*100:.1f}%)")
        print(f"   • Novelty Status: {'✅ Novel' if verification_result.get('is_novel', False) else '❌ Not Novel'}")
        print(f"   • Confidence Score: {confidence_score:.2f}")
        print(f"   • Novelty Threshold: {self.novelty_threshold}")
        print(f"   • Threshold Met: {'✅ Yes' if confidence_score >= self.novelty_threshold else '❌ No'}")

        # Show decision reasoning
        if agent_decision == "continue":
            print(f"\n🔄 CONTINUE DECISION:")
            if not verification_result.get('is_novel', False):
                print(f"   • Reason: Method lacks novelty - needs improvement")
            elif confidence_score < self.novelty_threshold:
                print(f"   • Reason: Confidence ({confidence_score:.2f}) below threshold ({self.novelty_threshold})")
            else:
                print(f"   • Reason: Agent determined further improvement possible")

            print(f"   • Action: Generate refinement feedback for next iteration")

        else:  # finalize
            print(f"\n🏁 FINALIZE DECISION:")
            if iteration_count >= max_iterations:
                print(f"   • Reason: Maximum iterations ({max_iterations}) reached")
            elif verification_result.get('is_novel', False) and confidence_score >= self.novelty_threshold:
                print(f"   • Reason: Novel method with high confidence achieved")
            else:
                print(f"   • Reason: Agent determined method ready for finalization")

            print(f"   • Action: Proceed to final output preparation")

        # Show generation history summary
        generation_history = state.get("generation_history", [])
        if generation_history:
            print(f"\n📈 GENERATION HISTORY SUMMARY:")
            for entry in generation_history:
                iter_num = entry.get("iteration", 0)
                is_refinement = entry.get("is_refinement", False)
                mode = "🔄 REFINEMENT" if is_refinement else "🆕 INITIAL"
                print(f"   Iteration {iter_num}: {mode}")

        print(f"{'='*80}\n")

        logger.info(f"Agent decision: {agent_decision}")

        # Update feedback history for tracking
        feedback_history = state.get("feedback_history", [])
        current_refinement_feedback = state.get("refinement_feedback", "")

        if agent_decision == "continue":
            # Always preserve current refinement feedback for next iteration
            if current_refinement_feedback:
                feedback_history.append(current_refinement_feedback)
                print(f"📚 Added current feedback to history (total: {len(feedback_history)})")
                print(f"🔄 Refinement feedback will be applied in next iteration")
            else:
                print("⚠️ No refinement feedback available for next iteration")

        result = {
            "agent_decision": agent_decision,
            "confidence_score": confidence_score,
            "feedback_history": feedback_history,
            # Preserve refinement feedback for next iteration if continuing
            "refinement_feedback": current_refinement_feedback if agent_decision == "continue" else ""
        }

        print_node_end("AGENT_DECISION", f"Decision: {agent_decision}")
        return result

    def _calculate_confidence_score(self, verification_result: Dict[str, Any]) -> float:
        """Calculate confidence score based on verification result"""
        if verification_result.get("is_novel", False):
            # Base score for novel methods
            base_score = 0.8

            # Adjust based on explanation quality/length (proxy for thoroughness)
            explanation = verification_result.get("explanation", "")
            if len(explanation) > 200:
                base_score += 0.1

            # Look for positive indicators in explanation
            positive_indicators = ["significant", "novel", "innovative", "advancement", "breakthrough"]
            for indicator in positive_indicators:
                if indicator.lower() in explanation.lower():
                    base_score += 0.02

            return min(base_score, 1.0)
        else:
            # Lower score for non-novel methods
            return 0.3

    @time_node("create_method_subgraph", "_refinement_feedback_node")
    def _refinement_feedback_node(self, state: CreateMethodSubgraphState) -> dict:
        """Generate specific feedback for method refinement using predefined REFINEMENT_FEEDBACK_PROMPT"""
        print_node_start("REFINEMENT_FEEDBACK")
        logger.info("---CreateMethodSubgraph Refinement Feedback Node---")

        verification_result = state["verification_result"]
        current_method = state["raw_generated_method"]
        iteration_count = state.get("iteration_count", 0)

        print("💭 Generating refinement feedback based on verification results...")
        print(f"📊 Input for feedback generation:")
        print(f"   Method Novel: {verification_result.get('is_novel', False)}")
        print(f"   Confidence: {verification_result.get('confidence', 0.0):.2f}")
        print(f"   Issues Count: {len(verification_result.get('specific_issues', []))}")
        print(f"   Related Papers: {len(verification_result.get('related_papers', []))}")

        refinement_feedback = refinement_feedback_node(
            verification_result=verification_result,
            current_method=current_method,
            iteration_count=iteration_count
        )

        print(f"📝 Feedback generated (length: {len(refinement_feedback)} chars)")

        # 🆕 DETAILED OUTPUT: Show full refinement feedback
        print(f"\n{'='*80}")
        print(f"📝 GENERATED REFINEMENT FEEDBACK (Iteration {iteration_count}):")
        print(f"{'='*80}")
        print(refinement_feedback)
        print(f"{'='*80}\n")

        # Log the detailed feedback sections for debugging
        feedback_sections = {
            "Immediate Improvements": "### Immediate Improvements Needed:",
            "Technical Enhancement": "### Technical Enhancement Suggestions:",
            "Differentiation Strategies": "### Differentiation Strategies:",
            "Novel Directions": "### Novel Directions to Explore:"
        }

        print("📋 FEEDBACK SECTIONS ANALYSIS:")
        for section_name, section_marker in feedback_sections.items():
            if section_marker in refinement_feedback:
                print(f"   ✅ {section_name} section included")
            else:
                print(f"   ❌ {section_name} section missing")

        # Count specific recommendations
        improvement_count = refinement_feedback.count("•") + refinement_feedback.count("-")
        print(f"📊 Total recommendations provided: {improvement_count}")

        logger.info(f"Generated refinement feedback: {refinement_feedback[:200]}...")

        result = {"refinement_feedback": refinement_feedback}
        print_node_end("REFINEMENT_FEEDBACK", f"Structured feedback generated ({len(refinement_feedback)} chars, {improvement_count} recommendations)")
        return result

    

    @time_node("create_method_subgraph", "_finalization_node")
    def _finalization_node(self, state: CreateMethodSubgraphState) -> dict:
        """Finalize the method and prepare output"""
        print_node_start("FINALIZATION")
        logger.info("---CreateMethodSubgraph Finalization Node---")

        # Use the current generated method as final
        final_method = state["raw_generated_method"]
        verification_result = state["verification_result"]
        total_iterations = state.get("iteration_count", 0)
        generation_history = state.get("generation_history", [])
        feedback_history = state.get("feedback_history", [])

        print(f"🎉 FINALIZATION SUMMARY:")
        print(f"   Total Iterations: {total_iterations}")
        print(f"   Final Method is Novel: {verification_result.get('is_novel', False)}")
        print(f"   Final Confidence: {verification_result.get('confidence', 0.0):.2f}")
        print(f"   Method Length: {len(final_method)} characters")
        print(f"   Feedback Applications: {len(feedback_history)}")

        # 🆕 DETAILED OUTPUT: Show final results
        print(f"\n{'='*80}")
        print(f"🏆 FINAL METHOD OUTPUT:")
        print(f"{'='*80}")
        print(final_method)
        print(f"{'='*80}\n")

        # Show process summary
        print(f"📊 PROCESS SUMMARY:")
        print(f"{'='*50}")

        # Iteration breakdown
        initial_generations = sum(1 for entry in generation_history if not entry.get("is_refinement", False))
        refinement_generations = sum(1 for entry in generation_history if entry.get("is_refinement", False))

        print(f"📈 Generation Breakdown:")
        print(f"   • Initial Generations: {initial_generations}")
        print(f"   • Refinement Generations: {refinement_generations}")
        print(f"   • Total Generations: {len(generation_history)}")

        # Final verification details
        print(f"\n🔍 Final Verification Details:")
        print(f"   • Novel: {'✅ YES' if verification_result.get('is_novel', False) else '❌ NO'}")
        print(f"   • Confidence: {verification_result.get('confidence', 0.0):.2f}")
        print(f"   • Significance: {verification_result.get('significance_level', 'medium')}")

        issues = verification_result.get('specific_issues', [])
        novel_aspects = verification_result.get('novel_aspects', [])
        if issues:
            print(f"   • Remaining Issues: {len(issues)}")
        if novel_aspects:
            print(f"   • Novel Aspects: {len(novel_aspects)}")

        # Show iteration timeline
        if generation_history:
            print(f"\n⏱️ Iteration Timeline:")
            for entry in generation_history:
                iter_num = entry.get("iteration", 0)
                is_refinement = entry.get("is_refinement", False)
                mode = "🔄 REFINEMENT" if is_refinement else "🆕 INITIAL"
                method_preview = entry.get("method", "")[:100] + "..."
                print(f"   {iter_num}. {mode}: {method_preview}")

        # Show applied feedback summary
        if feedback_history:
            print(f"\n📝 Applied Feedback Summary:")
            for i, feedback in enumerate(feedback_history, 1):
                feedback_preview = feedback[:150] + "..." if len(feedback) > 150 else feedback
                print(f"   Feedback {i}: {feedback_preview}")

        print(f"{'='*50}\n")

        logger.info(f"Finalized method after {total_iterations} iterations")

        result = {
            "new_method": final_method,
            "final_verification_result": verification_result,
            "total_iterations": total_iterations
        }

        print_node_end("FINALIZATION", f"Process completed after {total_iterations} iterations (Novel: {verification_result.get('is_novel', False)}, Confidence: {verification_result.get('confidence', 0.0):.2f})")
        return result

    def _route_after_decision(self, state: CreateMethodSubgraphState) -> str:
        """Route based on agent decision"""
        decision = state.get("agent_decision", "finalize")

        if decision == "continue":
            # Check if we need to generate refinement feedback first
            has_feedback = bool(state.get("refinement_feedback"))
            iteration_count = state.get("iteration_count", 0)
            verification_result = state.get("verification_result", {})
            confidence = verification_result.get("confidence", 0.0)
            is_novel = verification_result.get("is_novel", False)

            # If continuing but no feedback exists, generate it first
            if not has_feedback:
                print_routing_decision(
                    "AGENT_DECISION",
                    "REFINEMENT_FEEDBACK",
                    f"Continuing iteration {iteration_count + 1} - generating improvement feedback " +
                    f"(novel: {is_novel}, confidence: {confidence:.2f})"
                )
                return "refinement_feedback_node"
            else:
                print_routing_decision(
                    "AGENT_DECISION",
                    "GENERATOR",
                    f"Continuing iteration {iteration_count + 1} with existing feedback"
                )
                return "generator_node"
        else:
            print_routing_decision("AGENT_DECISION", "FINALIZATION", "Agent decided to finalize")
            return "finalization_node"





    def build_graph(self) -> CompiledGraph:
        print("🏗️ Building execution graph...")
        graph_builder = StateGraph(CreateMethodSubgraphState)

        # Add nodes
        graph_builder.add_node("initialization_node", self._initialization_node)
        graph_builder.add_node("generator_node", self._generator_node)
        graph_builder.add_node("novelty_verification_node", self._novelty_verification_node)
        graph_builder.add_node("refinement_feedback_node", self._refinement_feedback_node)
        graph_builder.add_node("agent_decision_node", self._agent_decision_node)
        graph_builder.add_node("finalization_node", self._finalization_node)

        # Define edges
        graph_builder.add_edge(START, "initialization_node")
        graph_builder.add_edge("initialization_node", "generator_node")
        graph_builder.add_edge("generator_node", "novelty_verification_node")

        # All verification results go to agent decision first
        graph_builder.add_edge("novelty_verification_node", "agent_decision_node")

        # Conditional routing based on agent decision
        graph_builder.add_conditional_edges(
            "agent_decision_node",
            self._route_after_decision,
            {
                "generator_node": "generator_node",
                "refinement_feedback_node": "refinement_feedback_node",
                "finalization_node": "finalization_node"
            }
        )

        # After refinement feedback, go back to generator
        graph_builder.add_edge("refinement_feedback_node", "generator_node")

        graph_builder.add_edge("finalization_node", END)

        print("✅ Graph built successfully!")
        print("\n📊 UPDATED EXECUTION FLOW:")
        print("   START → INITIALIZATION → GENERATOR → NOVELTY_VERIFICATION → AGENT_DECISION")
        print("                                                                    ↓")
        print("   ┌─────────────────────────────────────────────────────────────────┘")
        print("   ↓ (continue w/o feedback)     ↓ (continue w/ feedback)    ↓ (finalize)")
        print("   REFINEMENT_FEEDBACK    →    GENERATOR                   FINALIZATION")
        print("           ↓")
        print("       GENERATOR")

        return graph_builder.compile()



def main():
    llm_name = "o3-mini-2025-01-31"

    parser = argparse.ArgumentParser(description="Execute CreateMethodSubgraph")
    parser.add_argument("github_repository", help="Your GitHub repository")
    parser.add_argument(
        "branch_name", help="Your branch name in your GitHub repository"
    )
    args = parser.parse_args()

    # Create the method generator
    cm = AIScientistCreateMethodSubgraph(
        github_repository=args.github_repository,
        novelty_threshold=0.8,
        branch_name=args.branch_name,
        llm_name=llm_name,
        num_retrieve_paper=5
    )
    result = cm.run()
    print(f"result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running CreateMethodSubgraph: {e}")
        raise
