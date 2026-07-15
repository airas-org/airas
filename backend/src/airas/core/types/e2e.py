from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Status(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# TODO: Updates are required due to changes in the subgraph field.
class StepType(str, Enum):
    GENERATE_QUERIES = "generate_queries"
    SEARCH_PAPER_TITLES = "search_paper_titles"
    RETRIEVE_PAPERS = "retrieve_papers"
    GENERATE_HYPOTHESIS = "generate_hypothesis"
    GENERATE_EXPERIMENTAL_DESIGN = "generate_experimental_design"
    GENERATE_CODE = "generate_code"
    PUSH_CODE = "push_code"
    EXECUTE_TRIAL_EXPERIMENT = "execute_trial_experiment"
    EXECUTE_FULL_EXPERIMENT = "execute_full_experiment"
    EXECUTE_EVALUATION_WORKFLOW = "execute_evaluation_workflow"
    FETCH_EXPERIMENT_RESULTS = "fetch_experiment_results"
    ANALYZE_EXPERIMENT_RESULTS = "analyze_experiment_results"
    GENERATE_BIBFILE = "generate_bibfile"
    GENERATE_PAPER = "generate_paper"
    GENERATE_LATEX = "generate_latex"
    COMPILE_LATEX = "compile_latex"
    DONE = "done"


class E2EModel(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str

    created_by: UUID
    created_at: datetime = Field(
        default_factory=lambda: datetime.now().astimezone(),
    )

    status: Status = Status.PENDING
    current_step: Optional[StepType] = None
    error_message: Optional[str] = None
    result: dict[str, Any] = Field(default_factory=dict)

    last_updated_at: datetime = Field(
        default_factory=lambda: datetime.now().astimezone(),
    )

    github_url: Optional[str] = None
    schema_version: int = 1
