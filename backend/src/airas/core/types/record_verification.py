from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, computed_field


class DeclarationStatus(BaseModel):
    path: str = Field(
        description="hypotheses[h1]/claims[c1]/designs[d1]/runs[run-1]/params/epochs"
    )
    reason: str = Field(
        description="The evidence it was held against, what differed, or why it was not compared"
    )
    status: Literal["verified", "mismatch", "unverified"]
    evidence_path: str = Field(
        default="",
        description="Repository-relative file the declaration was held against",
    )


class RecordVerification(BaseModel):
    stage: Literal["prereg", "results"] = "prereg"
    declaration_statuses: list[DeclarationStatus] = Field(
        default_factory=list,
        description="Every live declaration once at least: verified / mismatch rows "
        "are what the gate compared, unverified rows are what it did not (record − coverage)",
    )

    @computed_field
    @property
    def problems(self) -> list[str]:
        return [s.reason for s in self.declaration_statuses if s.status == "mismatch"]

    @computed_field
    @property
    def ok(self) -> bool:
        return not self.problems

    def append_declaration_status(
        self,
        path: str,
        reason: str,
        status: Literal["verified", "mismatch", "unverified"],
        evidence_path: str = "",
    ) -> None:
        self.declaration_statuses.append(
            DeclarationStatus(
                path=path, reason=reason, status=status, evidence_path=evidence_path
            )
        )
