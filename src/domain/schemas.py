from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

# --- Enums ---


class Role(StrEnum):
    USER = 'user'
    ASSISTANT = 'assistant'
    TOOL = 'tool'


class RunStatus(StrEnum):
    PENDING = 'pending'
    RUNNING = 'running'
    DONE = 'done'
    FAILED = 'failed'


class ServiceStatus(StrEnum):
    OK = 'ok'
    DEGRADED = 'degraded'
    DOWN = 'down'


# --- Constrained types ---

NonEmptyStr = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
UserIdStr = Annotated[str, StringConstraints(min_length=1, max_length=255, strip_whitespace=True)]
SessionIdStr = Annotated[
    str, StringConstraints(min_length=1, max_length=255, strip_whitespace=True)
]
MessageStr = Annotated[str, StringConstraints(min_length=1, max_length=5000)]

# --- Request / Response ---


class AskRequest(BaseModel):
    user_id: UserIdStr
    session_id: SessionIdStr
    message: MessageStr


class AskResponse(BaseModel):
    run_id: str
    status_url: str


class RunStatusResponse(BaseModel):
    run_id: str
    status: RunStatus
    answer: str | None = None
    tools_used: list[str] = Field(default_factory=list)
    total_tokens: int | None = Field(default=None, ge=0)
    error: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class HealthResponse(BaseModel):
    status: ServiceStatus
    version: str
    uptime_seconds: float = Field(ge=0)
    checks: dict[str, ServiceStatus]


# --- Agent Internals ---


class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: Role
    content: NonEmptyStr
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ToolResult(BaseModel):
    tool_name: NonEmptyStr
    input: dict[str, object] = Field(default_factory=dict)
    output: str = ''
    error: str | None = None


class AgentRunResult(BaseModel):
    answer: str
    tools_used: list[str] = Field(default_factory=list)
    total_tokens: int = Field(default=0, ge=0)
    iterations: int = Field(default=0, ge=0)


class GuardrailResult(BaseModel):
    passed: bool
    reason: str | None = None


class ImageInput(BaseModel):
    """A single image attached to an agent request, already decoded from base64."""

    mime_type: Annotated[str, StringConstraints(min_length=1, max_length=64)]
    data: bytes = Field(..., description='Raw decoded image bytes')
