from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


# commit と AgentState を「どの step / iteration / run だったか」と一緒に結ぶ、
# 研究 workflow の trace の 1 行。step の begin と end で 1 行ずつ追記する。
# .research/trace/steps.jsonl に追記されていく。
class ResearchTraceEvent(BaseModel):
    kind: Literal["begin", "end"]
    step: str
    iteration: int = Field(ge=1, description="How many times this step has begun")
    timestamp: str
    head: Optional[str] = Field(default=None, description="HEAD when the event fired")
    run_ids: list[str] = Field(default_factory=list)
    reason: Optional[str] = None
    session_id: Optional[str] = None
    agent_state: Optional[str] = Field(
        default=None, description="Repo-relative path of the AgentState written"
    )
    intervention: Optional[dict[str, Any]] = Field(
        default=None,
        description=(
            "First step after a fork: how this agent differs from the one at "
            "the fork point (agent side) and what was changed on purpose "
            "(research side)"
        ),
    )


# 派生リポジトリの系譜。今の repo が「どの元 repo・commit・session から
# 派生したか」を 1 リンク分持ち、派生の派生はリンクを辿ってチェーンにする。
class DerivedFromRepository(BaseModel):
    repository: Optional[str] = None
    commit: str
    session_id: Optional[str] = None
