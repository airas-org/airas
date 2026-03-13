from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from airas.core.types.experimental_analysis import ExperimentalAnalysis
from airas.core.types.experimental_design import ExperimentalDesign
from airas.core.types.experimental_results import ExperimentalResults


class RunStage(str, Enum):
    SANITY = "sanity"
    PILOT = "pilot"
    FULL = "full"
    VISUALIZATION = "visualization"


class ExperimentCycleAction(str, Enum):
    SCALE_UP = "scale_up"
    REDESIGN = "redesign"
    ABORT = "abort"
    COMPLETE = "complete"


class ExperimentCycleDecision(BaseModel):
    action: ExperimentCycleAction = Field(
        ..., description="The decided next action for the experiment cycle"
    )
    reasoning: Optional[str] = Field(
        None, description="Explanation of why this action was chosen"
    )
    design_instruction: Optional[str] = Field(
        None,
        description="Instruction for refining the experimental design. Required when action is redesign.",
    )


class ExperimentCycle(BaseModel):
    experimental_design: ExperimentalDesign = Field(
        ..., description="Experimental design used in this cycle"
    )
    run_stage: RunStage = Field(
        ..., description="Stage at which the experiment was executed (pilot or full)"
    )
    experimental_results: Optional[ExperimentalResults] = Field(
        default=None, description="Results from the experiment execution"
    )
    experimental_analysis: Optional[ExperimentalAnalysis] = Field(
        default=None, description="Analysis of the experiment results"
    )
    decision: Optional[ExperimentCycleDecision] = Field(
        default=None, description="Decision made after analyzing this cycle's results"
    )


class ExperimentHistory(BaseModel):
    cycles: list[ExperimentCycle] = Field(
        default_factory=list,
        description="Append-only list of experiment cycles (pilot and full only; sanity is not recorded)",
    )
