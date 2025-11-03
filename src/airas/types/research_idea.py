from __future__ import annotations

import json
from typing import Optional

from pydantic import BaseModel


# ResearchHypothesis, immutable object
class GenerateIdea(BaseModel):
    open_problems: str
    method: str
    experimental_setup: str
    experimental_code: str
    expected_result: str
    expected_conclusion: str

    def to_formatted_json(self) -> str:
        data_dict = {
            "Open Problems": self.open_problems,
            "Methods": self.method,
            "Experimental Setup": self.experimental_setup,
            "Experimental Code": self.experimental_code,
            "Expected Result": self.expected_result,
            "Expected Conclusion": self.expected_conclusion,
        }
        return json.dumps(data_dict, ensure_ascii=False, indent=4)


class IdeaEvaluationResults(BaseModel):
    novelty_reason: str
    novelty_score: int
    significance_reason: str
    significance_score: int


class ResearchIdea(BaseModel):
    idea: GenerateIdea
    evaluation: Optional[IdeaEvaluationResults] = None

    # TODO?: Consider extracting it to utils/
    def to_formatted_string(self) -> str:
        parts = [f"Hypothesis:\n{self.idea.to_formatted_json()}"]
        if self.evaluation:
            parts.append(
                f"Novelty: {self.evaluation.novelty_reason}\n"
                f"Significance: {self.evaluation.significance_reason}"
            )
        return "\n".join(parts) + "\n"

    @classmethod
    def format_list(cls, ideas: list[ResearchIdea]) -> str:
        return (
            "".join(idea.to_formatted_string() for idea in ideas) or "No previous idea."
        )
