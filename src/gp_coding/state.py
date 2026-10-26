"""Workflow state management for gp-coding-plugin.

Maintains concurrency locking (single active workflow at a time),
step progression, waiting subagents, and persistence.
"""

from __future__ import annotations

import json
import os
from enum import Enum
from pathlib import Path
from typing import Any, Optional
from pydantic import BaseModel, Field


class WorkflowConflictError(Exception):
    """Raised when an attempt is made to start a coding workflow while another is active."""


class WorkflowStatus(str, Enum):
    IDLE = "IDLE"
    CLARIFYING = "CLARIFYING"
    SPECIFYING = "SPECIFYING"
    AWAITING_SPEC_APPROVAL = "AWAITING_SPEC_APPROVAL"
    PLANNING = "PLANNING"
    AWAITING_PLAN_APPROVAL = "AWAITING_PLAN_APPROVAL"
    DEVELOPING = "DEVELOPING"
    REVIEWING = "REVIEWING"
    AWAITING_MERGE_APPROVAL = "AWAITING_MERGE_APPROVAL"
    MERGING = "MERGING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

    def is_active(self) -> bool:
        return self not in (WorkflowStatus.IDLE, WorkflowStatus.COMPLETED, WorkflowStatus.FAILED)

    def is_waiting_user_input(self) -> bool:
        return self in (
            WorkflowStatus.AWAITING_SPEC_APPROVAL,
            WorkflowStatus.AWAITING_PLAN_APPROVAL,
            WorkflowStatus.AWAITING_MERGE_APPROVAL,
        )


class WorkflowState(BaseModel):
    workflow_id: str = Field(default="", description="Unique identifier for the current workflow run")
    status: WorkflowStatus = Field(default=WorkflowStatus.IDLE, description="Current status of the workflow")
    current_step: str = Field(default="", description="Identifier of the active subagent or step")
    waiting_agent: Optional[str] = Field(default=None, description="Name of the subagent waiting for user input")
    waiting_conversation_id: Optional[str] = Field(
        default=None, description="Conversation ID of the subagent waiting for message delivery"
    )
    repositories: list[str] = Field(default_factory=list, description="Target repository names or relative paths")
    active_develop_agents: dict[str, str] = Field(
        default_factory=dict, description="Mapping of repo_name -> develop subagent name or conversationId"
    )
    artifacts: dict[str, str] = Field(
        default_factory=dict, description="Artifact references (e.g. {'specification': path, 'plan': path})"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional context or state payloads")

    @classmethod
    def get_default_path(cls, artifact_dir: Optional[str] = None, conversation_id: Optional[str] = None) -> Path:
        """Resolve standard state file path."""
        if artifact_dir:
            p = Path(artifact_dir) / "coding_workflow_state.json"
            p.parent.mkdir(parents=True, exist_ok=True)
            return p
        if conversation_id:
            home = Path.home()
            p = home / ".gemini" / "antigravity-cli" / "brain" / conversation_id / "coding_workflow_state.json"
            p.parent.mkdir(parents=True, exist_ok=True)
            return p
        # Fallback to local .agents directory
        p = Path(".agents") / "coding_workflow_state.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    @classmethod
    def load(cls, path: Optional[Path] = None, artifact_dir: Optional[str] = None, conversation_id: Optional[str] = None) -> WorkflowState:
        target_path = path or cls.get_default_path(artifact_dir, conversation_id)
        if not target_path.exists():
            return cls()
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls.model_validate(data)
        except Exception:
            return cls()

    def save(self, path: Optional[Path] = None, artifact_dir: Optional[str] = None, conversation_id: Optional[str] = None) -> Path:
        target_path = path or self.get_default_path(artifact_dir, conversation_id)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))
        return target_path

    def start_workflow(self, workflow_id: str, repositories: Optional[list[str]] = None) -> None:
        """Initialize a new workflow. Enforces single active workflow constraint."""
        if self.status.is_active():
            raise WorkflowConflictError(
                f"Cannot start workflow '{workflow_id}': another workflow '{self.workflow_id}' "
                f"is currently active at step '{self.current_step}' (status: {self.status.value})."
            )
        self.workflow_id = workflow_id
        self.status = WorkflowStatus.CLARIFYING
        self.current_step = "coding-clarify"
        self.waiting_agent = None
        self.waiting_conversation_id = None
        self.repositories = repositories or []
        self.active_develop_agents = {}
        self.artifacts = {}
        self.metadata = {}

    def transition_to(
        self,
        status: WorkflowStatus,
        step: str,
        waiting_agent: Optional[str] = None,
        waiting_conversation_id: Optional[str] = None,
    ) -> None:
        """Transition workflow to the next step and optionally mark a waiting subagent."""
        self.status = status
        self.current_step = step
        self.waiting_agent = waiting_agent
        if waiting_conversation_id is not None:
            self.waiting_conversation_id = waiting_conversation_id

    def complete_workflow(self) -> None:
        """Mark workflow as successfully completed."""
        self.status = WorkflowStatus.COMPLETED
        self.current_step = "completed"
        self.waiting_agent = None
        self.waiting_conversation_id = None

    def fail_workflow(self, reason: str = "") -> None:
        """Mark workflow as failed."""
        self.status = WorkflowStatus.FAILED
        self.current_step = "failed"
        self.waiting_agent = None
        self.waiting_conversation_id = None
        self.metadata["failure_reason"] = reason
