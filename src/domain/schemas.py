from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

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


# --- Request / Response ---


class AskRequest(BaseModel):
    user_id: str
    session_id: str
    message: str


class AskResponse(BaseModel):
    run_id: str
    status_url: str


class RunStatusResponse(BaseModel):
    run_id: str
    status: RunStatus
    answer: str | None = None
    tools_used: list[str] = Field(default_factory=list)
    total_tokens: int | None = None
    error: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class HealthResponse(BaseModel):
    status: ServiceStatus
    version: str
    uptime_seconds: float
    checks: dict[str, ServiceStatus]


# --- Agent Internals ---


class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: Role
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ToolResult(BaseModel):
    tool_name: str
    input: dict = Field(default_factory=dict)
    output: str = ''
    error: str | None = None


class AgentRunResult(BaseModel):
    answer: str
    tools_used: list[str] = Field(default_factory=list)
    total_tokens: int = 0
    iterations: int = 0


class GuardrailResult(BaseModel):
    passed: bool
    reason: str | None = None
