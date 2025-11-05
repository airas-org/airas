from typing import Optional

from pydantic import BaseModel, Field

from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.research_iteration import ResearchIteration


class ResearchSession(BaseModel):
    hypothesis: ResearchHypothesis = Field(
        ..., description="The initial hypothesis that guides the research."
    )
    iterations: Optional[list[ResearchIteration]] = Field(
        None,
        description="A list of experimental cycles performed to test the hypothesis.",
    )

    @property
    def current_iteration(self) -> Optional[ResearchIteration]:
        return self.iterations[-1] if self.iterations else None

    @property
    def previous_iterations(self) -> list[ResearchIteration]:
        return self.iterations[:-1] if self.iterations else []
