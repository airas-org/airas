import json
import os
import os.path as osp
import time
from typing import Optional

from jinja2 import Environment
from pydantic import BaseModel, create_model

from airas.utils.api_client.llm_facade_client import LLMFacadeClient

# 各サブグラフの出力フィールドを定義
LLM_OUTPUT_FIELDS = {
    "retrieve_paper_subgraph": {},
    "generator_subgraph": {},
    "executor_subgraph": {
        "review_score_correctness": (float, ...),
        "review_score_novelty": (float, ...),
        "review_score_reproducibility": (float, ...),
        "review_feedback": (str, ...),
        "llm_return_to": (str, ...),
    },
    "writer_subgraph": {
        "review_score_clarity": (float, ...),
        "review_score_structure": (float, ...),
        "review_score_technical_depth": (float, ...),
        "review_feedback": (str, ...),
        "llm_return_to": (str, ...),
    },
}

REVIEW_ROUTING_RULES = {
    "retrieve_paper_subgraph": {},
    "generator_subgraph": {},
    "executor_subgraph": {"generator_subgraph"},
    "writer_subgraph": {},
}

SUBGRAPH_OUTPUTS_KEYS = {
    "generator_subgraph": [
        "verification_policy",
        "experiment_detail",
        "experiment_code",
    ],
    "executor_subgraph": ["output_text_data"],
    "writer_subgraph": ["tex_text"],
}


class DynamicModel(BaseModel):
    pass


class ReviewNode:
    def __init__(
        self,
        llm_name: str,
        save_dir: str,
        review_target: str,
        threshold: float = 3.5,
    ):
        self.llm_name = llm_name
        self.save_dir = save_dir
        self.review_target = review_target
        self.threshold = threshold

        self.env = Environment()
        self.dynamic_model = self._create_dynamic_model(DynamicModel)

        self.review_system_prompt = """
        You are an academic peer reviewer. 
        Your task is to evaluate research papers critically, identifying strengths and weaknesses, and suggesting improvements. 
        Your feedback should be constructive, specific, and actionable.

        **Pipeline Overview:**
        This system is an **automated research system** that combines existing papers to generate novel methodologies. 

        1. **retrieve_paper_subgraph**
            - Role: Retrieve base papers and patch papers as materials for generating a new methodology.

        2. **generator_subgraph**
            - Role: Synthesize a new methodology by combining elements from the retrieved papers.

        3. **executor_subgraph**
            - Role: Implement and execute the newly synthesized methodology through coding.

        4. **writer_subgraph**
            - Role: Use the synthesized methodology and execution results to generate a research paper, embedding it in LaTeX format.

        **Evaluation Criteria and Scoring:**
        1. Rate each evaluation criterion on a scale of 1.0 to 5.0, with increments of 0.1:
            - 1.0～2.0 = Needs significant improvement
            - 2.1～3.0 = Below average
            - 3.1～4.0 = Acceptable with revisions
            - 4.1～5.0 = High quality

            **Be conservative in awarding high scores**  
            A **5.0 rating** should be given only if the paper demonstrates **exceptional clarity, originality, methodology, and significance** with virtually no major flaws.

        2. For each criterion you score:
            - **Provide specific evidence** from the text or proposal to justify the score. 
            - Clearly explain how that evidence supports the numeric rating. 
            - Include **direct references (e.g., “In Section 3, the method is vaguely described...”)** or excerpts to pinpoint strong or weak points.
    
        **Feedback and Suggested Improvement:**
        1. **Identify at least three specific areas for improvement** and provide **clear revision suggestions in the `review_feedback` field**:
            - **What aspects contributed to this score?**
            - **What needs to be changed?**
            - **How should it be revised?**
            - **Why will this improve the paper?**

        **Routing Rules*:*
        1. If the paper requires further work, suggest revisiting an earlier subgraph or re-running the current subgraph.
            - **Do not route to any subgraph that comes AFTER the current one in the pipeline.**

        2. Additional custom restrictions:
            - The `{{ REVIEW_ROUTING_RULES }}` dictionary defines specific routing constraints. The **keys represent the review criteria**, and the **values represent possible routing destinations** for revisions.
            - If the value is empty (`[]`), there are no additional restrictions, but **only previous subgraphs in the pipeline can be revisited** (i.e., the process cannot move forward past its current stage).


        **Output Format:**
        Your response must be in the following JSON format:
        { 
        "review_score_xxx": <1.0-5.0>, 
        "review_score_yyy": <1.0-5.0>, 
        "review_score_zzz": <1.0-5.0>, 
        "review_feedback": "<Your feedback here>" 
        "llm_return_to": "<subgraph_name to be re-executed>"
        }   
        """

        self.review_prompt_dict = {
            "retrieve_paper_subgraph": """
            """,
            "generator_subgraph": """
            """,
            "executor_subgraph": """
            Evaluate the experimental implementation and execution based on the following criteria:

            **Evaluation Criteria:**
            - **review_score_correctness (1.0-5.0)**: Does the implementation correctly execute the intended methodology? Are the results consistent with expectations?
            - **review_score_novelty (1.0-5.0)**: Does the implementation introduce novel experimental techniques, optimizations, or unique approaches?
            - **review_score_reproducibility (1.0-5.0)**: Can the implementation be easily replicated by other researchers based on the provided information?
            - **review_feedback**: Provide feedback on the strengths and weaknesses of the implementation and suggest improvements.
            - **llm_return_to**: "<subgraph_name to be re-executed>"

            **Review Content（JSON）:**
            {{ content }}
            """,
            "writer_subgraph": """
            The following is a research paper written in LaTeX format. Evaluate its quality based on the following criteria:

            **Evaluation Criteria:**
            - **review_score_clarity (1.0-5.0)**: Is the writing clear and understandable?
            - **review_score_structure (1.0-5.0)**: Is the structure and organization of the paper logical and coherent?
            - **review_score_technical_depth (1.0-5.0)**: Does the paper provide sufficient technical depth and explanation?
            - **review_feedback**: Provide feedback on the strengths and weaknesses of the paper and suggest improvements.
            - **llm_return_to**:  "<subgraph_name to be re-executed>"

            **Review Content（JSON）:**
            {{ content }}
            """,
        }

    def _create_dynamic_model(self, base_model: BaseModel) -> BaseModel:
        """review_target に応じた動的な Pydantic モデルを生成する"""
        fields = LLM_OUTPUT_FIELDS.get(self.review_target, {})
        return create_model(
            f"LLMOutput_{self.review_target.capitalize()}",
            **fields,
            __base__=base_model,
        )

    def _construct_review_content(self, state: dict) -> str:
        current_subgraph = self.review_target
        current_output = {
            key: state.get(key, "<missing_data>")
            for key in SUBGRAPH_OUTPUTS_KEYS.get(current_subgraph, [])
        }

        previous_subgraph_outputs = {}

        for subgraph_name, keys in SUBGRAPH_OUTPUTS_KEYS.items():
            if subgraph_name == current_subgraph:
                break
            subgraph_data = {key: state.get(key, "<missing_data>") for key in keys}
            previous_subgraph_outputs[subgraph_name] = subgraph_data

        review_content = {
            "current_subgraph": current_subgraph,
            "current_output": current_output,
            "previous_subgraph_outputs": previous_subgraph_outputs,
        }

        return json.dumps(review_content, indent=2)

    def _review(self, content: str) -> Optional[tuple[str, dict, str]]:
        client = LLMFacadeClient(self.llm_name)
        if self.review_target not in self.review_prompt_dict:
            raise ValueError(f"Invalid review target: {self.review_target}")

        system_prompt_rendered = self.env.from_string(self.review_system_prompt).render(
            {"REVIEW_ROUTING_RULES": REVIEW_ROUTING_RULES}
        )
        user_prompt_rendered = self.env.from_string(
            self.review_prompt_dict[self.review_target]
        ).render({"content": content})
        max_retries = 3
        for attempt in range(max_retries):
            try:
                messages = system_prompt_rendered + user_prompt_rendered
                structured_output, cost = client.structured_outputs(
                    message=messages,
                    data_model=self.dynamic_model,
                )
                if structured_output is None:
                    raise ValueError("Error: No response from the llm model.")
                review_feedback = structured_output.get("review_feedback", "")
                review_scores = {
                    key: value
                    for key, value in structured_output.items()
                    if key.startswith("review_score_") and isinstance(value, float)
                }
                llm_return_to = structured_output.get("llm_return_to", None)
                return review_feedback, review_scores, llm_return_to

            except Exception as e:
                print(f"[Attempt {attempt+1}/{max_retries}] Unexpected error: {e}")
        print("Exceeded maximum retries for LLM call.")
        return None

    def _review_judgement(
        self, review_scores: dict, llm_return_to: str
    ) -> Optional[str]:
        # 1) すべてのスコアが threshold 以上なら合格 → return None（= 次に進む）
        if all(score >= self.threshold for score in review_scores.values()):
            return None

        # 2) llm_return_to の値が想定外ならフォールバック
        valid_subgraphs = set(LLM_OUTPUT_FIELDS.keys())
        if llm_return_to not in valid_subgraphs:
            print(
                f"Warning: Unexpected llm_return_to value '{llm_return_to}', defaulting to '{self.review_target}'"
            )
            return self.review_target

        # 3) REVIEW_ROUTING_RULES による制限を適用する
        allowed_routes = REVIEW_ROUTING_RULES.get(self.review_target, set())
        if allowed_routes and llm_return_to not in allowed_routes:
            print(
                f"Warning: subgraph '{self.review_target}' can only route to {allowed_routes}, "
                f"but got '{llm_return_to}', Fallback to '{self.review_target}'"
            )
            return self.review_target

        return llm_return_to

    def _save_review_log(
        self,
        review_routing: Optional[str],
        review_scores: dict,
        review_feedback: str,
        content: str,
    ):
        # TODO: 同じワークフロー内で生成されるレビューを1つのファイルに集約できるようにする。

        os.makedirs(self.save_dir, exist_ok=True)

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        review_file = osp.join(self.save_dir, f"{timestamp}_review.json")

        try:
            review_content = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            review_content = {"raw_content": content}

        review_data = {
            "timestamp": timestamp,
            "review_target": self.review_target,
            "review_routing": "Pass" if review_routing is None else review_routing,
            "review_scores": review_scores,
            "review_feedback": review_feedback,
            "content": review_content,
        }
        try:
            with open(review_file, "w") as f:
                json.dump(review_data, f, indent=4)
            print(f"Review log saved to {review_file}")
        except Exception as e:
            print(f"Failed to save review log: {e}")

    def execute(self, state: dict) -> tuple[Optional[str], str]:
        current_output_keys = SUBGRAPH_OUTPUTS_KEYS.get(self.review_target, [])
        if any(state.get(key) is None for key in current_output_keys):
            print(f"Skipping review: Missing data for {self.review_target}")
            return None, "Skipped review due to missing data."

        content = self._construct_review_content(state)
        print(f"content: {content}")

        print("Reviewing content...")
        review_result = self._review(content)
        if not review_result:
            raise RuntimeError(
                "Failed to review content. The LLM returned an empty response."
            )

        review_feedback, review_scores, llm_return_to = review_result
        review_routing = self._review_judgement(review_scores, llm_return_to)
        self._save_review_log(review_routing, review_scores, review_feedback, content)

        return review_routing, review_feedback
