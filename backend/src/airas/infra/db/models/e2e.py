from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, String
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlmodel import Field, SQLModel


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


class E2EModel(SQLModel, table=True):
    __tablename__ = "e2e_results"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    title: str = Field(nullable=False)

    created_by: UUID = Field(nullable=False, index=True)
    created_at: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
        default_factory=lambda: datetime.now().astimezone(),
    )

    status: Status = Field(
        sa_column=Column(SqlEnum(Status, name="status"), nullable=False),
        default=Status.PENDING,
    )
    current_step: Optional[StepType] = Field(
        default=None,
        sa_column=Column(SqlEnum(StepType, name="step_type"), nullable=True),
    )
    error_message: Optional[str] = Field(
        default=None, sa_column=Column(String, nullable=True)
    )
    result: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSONB, nullable=False)
    )

    last_updated_at: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
        default_factory=lambda: datetime.now().astimezone(),
    )

    github_url: Optional[str] = Field(
        default=None, sa_column=Column(String, nullable=True)
    )
    schema_version: int = Field(default=1, nullable=False)
