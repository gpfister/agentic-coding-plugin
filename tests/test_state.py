"""Tests for gp_coding WorkflowState management and concurrency locking."""

import pytest
from pathlib import Path
from gp_coding.state import WorkflowState, WorkflowStatus, WorkflowConflictError


def test_initial_state_is_idle():
    state = WorkflowState()
    assert state.status == WorkflowStatus.IDLE
    assert not state.status.is_active()
    assert not state.status.is_waiting_user_input()


def test_start_workflow_success_and_conflict():
    state = WorkflowState()
    state.start_workflow(workflow_id="wf-1", repositories=["repo-a"])
    assert state.status == WorkflowStatus.CLARIFYING
    assert state.current_step == "coding-clarify"
    assert state.status.is_active()

    # Attempting to start a second workflow while wf-1 is active must raise WorkflowConflictError
    with pytest.raises(WorkflowConflictError) as exc_info:
        state.start_workflow(workflow_id="wf-2")
    assert "another workflow 'wf-1' is currently active" in str(exc_info.value)


def test_workflow_transitions_and_waiting():
    state = WorkflowState()
    state.start_workflow("wf-1")

    # Move to coding-specify awaiting approval
    state.transition_to(
        status=WorkflowStatus.AWAITING_SPEC_APPROVAL,
        step="coding-specify",
        waiting_agent="coding-specify",
        waiting_conversation_id="conv-spec-123",
    )
    assert state.status.is_waiting_user_input()
    assert state.waiting_agent == "coding-specify"
    assert state.waiting_conversation_id == "conv-spec-123"

    # Move to planning
    state.transition_to(
        status=WorkflowStatus.AWAITING_PLAN_APPROVAL,
        step="coding-plan",
        waiting_agent="coding-plan",
        waiting_conversation_id="conv-plan-456",
    )
    assert state.status.is_waiting_user_input()
    assert state.waiting_agent == "coding-plan"

    # Complete workflow
    state.complete_workflow()
    assert state.status == WorkflowStatus.COMPLETED
    assert not state.status.is_active()
    assert state.waiting_agent is None

    # Now a new workflow can start cleanly
    state.start_workflow("wf-2")
    assert state.workflow_id == "wf-2"
    assert state.status == WorkflowStatus.CLARIFYING


def test_state_persistence_roundtrip(tmp_path: Path):
    state_file = tmp_path / "state.json"
    state = WorkflowState()
    state.start_workflow("wf-persist", repositories=["frontend", "backend"])
    state.transition_to(
        status=WorkflowStatus.AWAITING_SPEC_APPROVAL,
        step="coding-specify",
        waiting_agent="coding-specify",
        waiting_conversation_id="conv-abc",
    )
    state.save(path=state_file)

    loaded = WorkflowState.load(path=state_file)
    assert loaded.workflow_id == "wf-persist"
    assert loaded.status == WorkflowStatus.AWAITING_SPEC_APPROVAL
    assert loaded.waiting_agent == "coding-specify"
    assert loaded.waiting_conversation_id == "conv-abc"
    assert loaded.repositories == ["frontend", "backend"]
