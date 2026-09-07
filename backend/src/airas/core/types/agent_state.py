"""The agent side of a fork point.

A fork point is a commit holding the experiment repository *and* the state
of the agent that produced it, so anyone can clone that commit and continue
from the same place — with the same agent, a different model or harness,
or a different method. The agent's state is its harness (who is running)
and its session (what it saw and did); both are stored under
`.research/sessions/<harness>/<session_id>/`.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Harness = Literal["claude", "codex"]


class AgentState(BaseModel):
    harness: HarnessState
    session: SessionState


class HarnessState(BaseModel):
    kind: Harness
    version: Optional[str] = None
    model: Optional[str] = None
    files: dict[str, str] = Field(
        default_factory=dict,
        description="Settings and instruction files by original path; secrets masked",
    )
    memory: dict[str, str] = Field(
        default_factory=dict, description="Memory files by name"
    )
    plugin: Optional[PluginRef] = None


class PluginRef(BaseModel):
    root: str
    version: Optional[str] = None
    skills_sha256: str = Field(description="Hash of every file under skills/")


class SessionState(BaseModel):
    session_id: str
    transcripts: list[str] = Field(
        description="Raw transcript files copied verbatim, repo-relative"
    )


# MCP サーバーに「今どのセッションから呼ばれているか」を知らせる橋渡し情報。
# hook がセッション開始時に ~/.airas/sessions/ に書き、end_step がこれを
# 読んで live session（cwd、transcript の場所など）を特定する。
class SessionPointer(BaseModel):
    harness: Harness
    session_id: str
    cwd: str
    transcript_path: Optional[str] = None
    model: Optional[str] = None
    plugin_root: Optional[str] = None
