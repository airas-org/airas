from typing import Optional

from pydantic import BaseModel, Field

from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.research_iteration import ResearchIteration


class ResearchSession(BaseModel):
    hypothesis: ResearchHypothesis = Field(
        ..., description="The initial hypothesis that guides the research."
    )
    iterations: list[ResearchIteration] = Field(
        default_factory=list,
        description="A list of experimental cycles performed to test the hypothesis.",
    )
    best_iteration_id: Optional[int] = Field(
        None,
        description="The iteration_id with the best performance gap (selected for paper writing)",
    )

    @property
    def current_iteration(self) -> Optional[ResearchIteration]:
        return self.iterations[-1] if self.iterations else None

    @property
    def previous_iterations(self) -> list[ResearchIteration]:
        return self.iterations[:-1] if self.iterations else []

    @property
    def best_iteration(self) -> Optional[ResearchIteration]:
        if self.best_iteration_id is None:
            return self.current_iteration

        return next(
            (
                iter
                for iter in self.iterations
                if iter.iteration_id == self.best_iteration_id
            ),
            self.current_iteration,
        )
