from logging import getLogger
from airas.types.paper import CandidatePaperInfo
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL, LLMFacadeClient
from airas.core.create.create_method_subgraph.prompt.PromptManager import PromptManager
from airas.core.retrieve.retrieve_paper_from_query_subgraph.nodes.retrieve_arxiv_text_node import RetrievearXivTextNode
from airas.core.retrieve.retrieve_paper_from_query_subgraph.nodes.arxiv_api_node import ArxivNode
from airas.core.retrieve.retrieve_paper_from_query_subgraph.nodes.summarize_paper_node import summarize_paper_node, summarize_paper_prompt_add
from typing import Any, Dict, List
import os
import json

logger = getLogger(__name__)


# Pure novelty verification function (separated from refinement)
def pure_novelty_verification_node(
    llm_name: LLM_MODEL,
    raw_generated_method: str,
    base_method_text: CandidatePaperInfo,
    add_method_texts: list[CandidatePaperInfo],
    num_retrieve_paper: int,
    client: LLMFacadeClient | None = None,
) -> Dict[str, Any]:
    """
    Pure novelty verification without method refinement.
    Only assesses whether the method is novel and provides explanation.
    """
    print("🔍 Starting pure novelty verification...")

    if client is None:
        client = LLMFacadeClient(llm_name=llm_name)


    # Create temporary directory for paper storage if it doesn't exist
    papers_dir = os.path.join(os.getcwd(), "temp_papers")
    os.makedirs(papers_dir, exist_ok=True)
    print(f"📁 Using papers directory: {papers_dir}")

    # Step 1: Extract key terms for searching
    print("🔤 Extracting search terms from generated method...")
    key_terms = _extract_search_terms(client, raw_generated_method)
    print(f"🔍 Search terms: {key_terms.get('key_terms', [])}")

    # Step 2: Search for related papers on arXiv using ArxivNode
    print(f"📚 Searching arXiv for related papers (limit: {num_retrieve_paper})...")
    arxiv_node = ArxivNode(num_retrieve_paper=num_retrieve_paper)
    search_results = arxiv_node.execute(queries=key_terms["key_terms"])

    # Skip papers that were used as base or add methods
    used_arxiv_ids = _get_used_arxiv_ids(base_method_text, add_method_texts)
    print(f"🚫 Excluding {len(used_arxiv_ids)} papers used in method creation")

    # Process and filter search results (same as original)
    if search_results and isinstance(search_results[0], list):
        flattened_results = []
        for query_results in search_results:
            flattened_results.extend(query_results)
        search_results = flattened_results

    # Remove duplicates and filter out used papers
    seen_arxiv_ids = set()
    filtered_results = []
    for paper in search_results:
        arxiv_id = paper.get("arxiv_id")
        if arxiv_id and arxiv_id not in used_arxiv_ids and arxiv_id not in seen_arxiv_ids:
            filtered_results.append(paper)
            seen_arxiv_ids.add(arxiv_id)

    print(f"📄 Found {len(filtered_results)} unique related papers to analyze")

    # Step 3: Analyze related papers
    related_papers = []
    retrieve_arxiv_text_node = RetrievearXivTextNode(papers_dir=papers_dir)

    for i, paper in enumerate(filtered_results):
        arxiv_id = paper.get("arxiv_id", "")
        if not arxiv_id:
            continue

        print(f"📖 Processing paper {i+1}/{len(filtered_results)}: {arxiv_id}")
        try:
            full_text = retrieve_arxiv_text_node.execute(arxiv_url=paper.get("arxiv_url", ""))
            main_contributions, methodology, experimental_setup, limitations, future_research_directions = summarize_paper_node(
                llm_name=llm_name,
                prompt_template=summarize_paper_prompt_add,
                paper_text=full_text,
            )

            related_papers.append({
                "arxiv_id": arxiv_id,
                "title": paper.get("title", ""),
                "summary": {
                    "main_contributions": main_contributions,
                    "methodology": methodology,
                    "experimental_setup": experimental_setup,
                    "limitations": limitations,
                    "future_research_directions": future_research_directions
                }
            })
            print(f"✅ Successfully processed {arxiv_id}")
        except Exception as e:
            print(f"❌ Error processing paper {arxiv_id}: {e}")
            logger.warning(f"Error processing paper {arxiv_id}: {e}")

    # Step 4: Pure novelty verification (no refinement)
    print(f"⚖️ Conducting novelty assessment against {len(related_papers)} papers...")

    try:
        verification_result = _pure_novelty_assessment(
            client=client,
            raw_generated_method=raw_generated_method,
            base_method_text=base_method_text,
            add_method_texts=add_method_texts,
            related_papers=related_papers,
        )

        # Ensure verification_result is a valid dictionary
        if verification_result is None:
            print("⚠️ Novelty assessment returned None, creating default result")
            verification_result = {
                "is_novel": True,
                "confidence": 0.5,
                "explanation": "Assessment returned None result. Assuming novel by default.",
                "specific_issues": [],
                "novel_aspects": [],
                "overlap_analysis": {},
                "significance_level": "medium"
            }
        elif not isinstance(verification_result, dict):
            print(f"⚠️ Novelty assessment returned unexpected type: {type(verification_result)}")
            verification_result = {
                "is_novel": True,
                "confidence": 0.5,
                "explanation": f"Assessment returned unexpected type: {type(verification_result)}. Assuming novel by default.",
                "specific_issues": [],
                "novel_aspects": [],
                "overlap_analysis": {},
                "significance_level": "medium"
            }

        # Add related papers to the result
        verification_result["related_papers"] = related_papers
        print(f"✅ Novelty verification completed")
        return verification_result

    except Exception as e:
        print(f"❌ Error in novelty verification: {e}")
        logger.error(f"Error in novelty verification: {e}")
        return {
            "is_novel": True,
            "confidence": 0.5,
            "explanation": f"Error during novelty verification: {str(e)}. Assuming novel by default.",
            "specific_issues": [f"Verification error: {str(e)}"],
            "novel_aspects": [],
            "overlap_analysis": {},
            "significance_level": "medium",
            "related_papers": related_papers or []
        }



def _pure_novelty_assessment(
    client: LLMFacadeClient,
    raw_generated_method: str,
    base_method_text: CandidatePaperInfo,
    add_method_texts: list[CandidatePaperInfo],
    related_papers: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Pure novelty assessment without providing refinement suggestions using predefined prompt.
    """
    print("🧠 Running novelty assessment with predefined PURE_NOVELTY_VERIFICATION_PROMPT...")

    try:
        # Format related papers for the prompt
        formatted_papers = []
        for paper in related_papers:
            if paper is None:
                print("⚠️ Skipping None paper in related_papers")
                continue

            summary = paper.get("summary", {})
            if isinstance(summary, dict):
                formatted_paper = {
                    "title": paper.get("title", ""),
                    "arxiv_id": paper.get("arxiv_id", ""),
                    "summary": (
                        f"Main Contributions: {summary.get('main_contributions', '')}\n"
                        f"Methodology: {summary.get('methodology', '')}\n"
                        f"Experimental Setup: {summary.get('experimental_setup', '')}\n"
                        f"Limitations: {summary.get('limitations', '')}\n"
                        f"Future Research Directions: {summary.get('future_research_directions', '')}"
                    )
                }
            else:
                formatted_paper = {
                    "title": paper.get("title", ""),
                    "arxiv_id": paper.get("arxiv_id", ""),
                    "summary": str(summary)
                }
            formatted_papers.append(formatted_paper)

        print(f"📝 Formatted {len(formatted_papers)} papers for assessment")

        # Ensure all input data is valid
        if base_method_text is None:
            base_method_text = "No base method provided"
        if add_method_texts is None:
            add_method_texts = []

        # Prepare template data
        template_data = {
            "raw_generated_method": raw_generated_method or "No method provided",
            "base_method_text": base_method_text,
            "add_method_texts": add_method_texts,
            "related_papers": formatted_papers,
        }

        print("🔧 Rendering assessment prompt using PromptManager...")

        # Use PromptManager to render the prompt
        messages = PromptManager.render_prompt(
            PromptManager.get_novelty_verification_prompt,
            **template_data
        )

        print("🤖 Sending request to LLM for novelty assessment...")
        output, _ = client.generate(message=messages)

        print("📋 Parsing LLM response...")
        try:
            result = json.loads(output)
            print(f"✅ LLM assessment completed successfully")

            # Validate the result structure
            if not isinstance(result, dict):
                raise ValueError("Result is not a dictionary")

            # Ensure required fields exist with defaults
            validated_result = {
                "is_novel": result.get("is_novel", True),
                "confidence": result.get("confidence", 0.5),
                "explanation": result.get("explanation", "Assessment completed but no detailed explanation provided."),
                "specific_issues": result.get("specific_issues", []),
                "novel_aspects": result.get("novel_aspects", []),
                "overlap_analysis": result.get("overlap_analysis", {
                    "major_overlaps": [],
                    "minor_similarities": [],
                    "unique_contributions": []
                }),
                "significance_level": result.get("significance_level", "medium")
            }

            return validated_result

        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"🔍 Raw LLM output (first 500 chars): {output[:500]}...")
            return {
                "is_novel": True,
                "confidence": 0.5,
                "explanation": f"Unable to parse LLM response as JSON. Raw response: {output[:200]}...",
                "specific_issues": ["JSON parsing error in assessment"],
                "novel_aspects": [],
                "overlap_analysis": {
                    "major_overlaps": [],
                    "minor_similarities": [],
                    "unique_contributions": []
                },
                "significance_level": "medium"
            }

    except Exception as e:
        print(f"❌ Critical error in novelty assessment: {e}")
        print(f"🔍 Error type: {type(e)}")
        logger.warning(f"Error in novelty assessment: {e}")
        return {
            "is_novel": True,
            "confidence": 0.5,
            "explanation": f"Critical error during novelty assessment: {str(e)}. Assuming novel by default.",
            "specific_issues": [f"Assessment error: {str(e)}"],
            "novel_aspects": [],
            "overlap_analysis": {
                "major_overlaps": [],
                "minor_similarities": [],
                "unique_contributions": []
            },
            "significance_level": "medium"
        }

# Helper functions (reused from original)
def _extract_search_terms(client: LLMFacadeClient, raw_generated_method: str) -> dict[str, str | list[str]]:
    """Extract key search terms from the generated method."""
    print("🔤 Analyzing method to extract search terms...")

    prompt = f"""
    Analyze the following proposed method and extract 3-5 key technical terms or concepts that define its novelty.
    Then, create a search query suitable for arXiv to find related papers.

    METHOD:
    {raw_generated_method}

    Output the result as a JSON object with the following format:
    {{
        "key_terms": ["term1", "term2", "term3"],
        "search_query": "constructed query for arXiv"
    }}
    """

    output, _ = client.generate(message=prompt)

    try:
        search_terms = json.loads(output)
        print(f"✅ Extracted search terms successfully")
        return search_terms
    except Exception as e:
        print(f"⚠️ Error parsing search terms: {e}, using defaults")
        logger.warning(f"Error parsing search terms: {e}")
        return {
            "key_terms": ["diffusion model", "sampling", "optimization"],
            "search_query": "diffusion model optimization sampling schedule"
        }


def _get_used_arxiv_ids(base_method_text: CandidatePaperInfo, add_method_texts: list[CandidatePaperInfo]) -> List[str]:
    """Extract arXiv IDs from base and add method texts to avoid reusing them."""
    print("🔍 Extracting arXiv IDs from base and additional methods...")
    used_ids = []

    try:
        if isinstance(base_method_text, str):
            try:
                base_data = json.loads(base_method_text.strip().strip("'\""))
                if "arxiv_id" in base_data:
                    used_ids.append(base_data["arxiv_id"])
                    print(f"📄 Found base method arXiv ID: {base_data['arxiv_id']}")
            except Exception as e:
                logger.warning(f"Error extracting arXiv ID from base method: {e}")

        for i, method_text in enumerate(add_method_texts):
            try:
                if isinstance(method_text, str):
                    add_data = json.loads(method_text.strip().strip("'\""))
                    if "arxiv_id" in add_data:
                        used_ids.append(add_data["arxiv_id"])
                        print(f"📄 Found additional method {i+1} arXiv ID: {add_data['arxiv_id']}")
            except Exception as e:
                logger.warning(f"Error extracting arXiv ID from add method: {e}")
    except Exception as e:
        logger.warning(f"Error extracting arXiv IDs: {e}")

    print(f"📋 Total arXiv IDs to exclude: {len(used_ids)}")
    return used_ids
