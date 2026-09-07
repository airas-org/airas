from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


# commit と AgentState を「どの step だったか」と一緒に結ぶ、研究 workflow の
# trace の 1 行。ハーネスの hook が .research/trace/steps.jsonl に追記する:
# step はスキルに入ったとき（Claude Code の Skill 呼び出し）、capture はターン
# 終了ごとの AgentState の取り込みと commit。
class ResearchTraceEvent(BaseModel):
    kind: Literal["step", "capture"]
    timestamp: str
    session_id: str
    head: Optional[str] = Field(default=None, description="HEAD when the event fired")
    step: Optional[str] = Field(default=None, description="Skill entered (kind=step)")
    iteration: Optional[int] = Field(
        default=None, ge=1, description="How many times this step has begun"
    )
    agent_state: Optional[str] = Field(
        default=None, description="Repo-relative path of the AgentState written"
    )
    intervention: Optional[dict[str, Any]] = Field(
        default=None,
        description=(
            "First capture after a fork: how this harness differs from the one "
            "at the fork point"
        ),
    )


# 派生リポジトリの系譜。今の repo が「どの元 repo・commit・session から
# 派生したか」を 1 リンク分持ち、派生の派生はリンクを辿ってチェーンにする。
class DerivedFromRepository(BaseModel):
    repository: Optional[str] = None
    commit: str
    session_id: Optional[str] = None
