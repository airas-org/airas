from __future__ import annotations

import json
from typing import Optional

from pydantic import BaseModel, Field


class ResearchHypothesis(BaseModel):
    open_problems: str
    method: str
    experimental_setup: str
    primary_metric: str = Field(
        description=(
            "One standard, machine-extractable metric name. The GAP between "
            "the proposal and its baselines is computed from this one."
        )
    )
    supporting_metrics: list[str] = Field(
        default_factory=list,
        description=(
            "Further metric names reported alongside the primary one, for "
            "research whose claim needs more than a single number. Reported "
            "separately; never aggregated into primary_metric."
        ),
    )
    # A sketch written before the repository, the data, or the code template
    # have been seen, kept only to convey the idea. The real implementation
    # replaces it, and the paper-writing step reads this, so an unfaithful
    # sketch surfaces later as a methods section that describes code nobody
    # ran. Empty is better than wrong.
    experimental_code: str = ""
    expected_result: str
    expected_conclusion: str

    def to_formatted_json(self) -> str:
        data_dict = {
            "Open Problems": self.open_problems,
            "Methods": self.method,
            "Experimental Setup": self.experimental_setup,
            "Primary Metric": self.primary_metric,
            "Supporting Metrics": self.supporting_metrics,
            "Experimental Code": self.experimental_code,
            "Expected Result": self.expected_result,
            "Expected Conclusion": self.expected_conclusion,
        }
        return json.dumps(data_dict, ensure_ascii=False, indent=4)


class HypothesisEvaluation(BaseModel):
    novelty_reason: str
    novelty_score: int
    significance_reason: str
    significance_score: int


class EvaluatedHypothesis(BaseModel):
    hypothesis: ResearchHypothesis
    evaluation: Optional[HypothesisEvaluation] = None

    # TODO?: Consider extracting it to utils/
    def to_formatted_string(self) -> str:
        parts = [f"Hypothesis:\n{self.hypothesis.to_formatted_json()}"]
        if self.evaluation:
            parts.append(
                f"Novelty: {self.evaluation.novelty_reason}\n"
                f"Significance: {self.evaluation.significance_reason}"
            )
        return "\n".join(parts) + "\n"

    @classmethod
    def format_list(cls, hypotheses: list[EvaluatedHypothesis]) -> str:
        return (
            "".join(hypothesis.to_formatted_string() for hypothesis in hypotheses)
            or "No previous hypotheses."
        )
