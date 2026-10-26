"""Coding Orchestrator ADK Workflow.

Orchestrates the 6-stage development lifecycle:
coding_clarify -> coding_specify -> coding_plan -> coding_develop -> coding_review -> coding_merge

Built using Google ADK 2.0 Workflow API, coordinating Antigravity subagents and
maintaining the single active workflow constraint.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional
from google.adk.events.event import Event, EventActions
from google.adk.workflow import Workflow, START

from gp_coding.state import WorkflowState, WorkflowStatus, WorkflowConflictError
from gp_coding.schemas import (
    ClarificationSummary,
    SpecificationDocument,
    PlanDocument,
    DevelopReport,
    ReviewReport,
    MergeReport,
)

ORCHESTRATOR_DESCRIPTION = """Coding Orchestrator workflow (@coding).
Guides feature requests through clarification, specification, multi-repo planning,
isolated development, cross-repo consistency review, and automated merging.
"""


# ---------------------------------------------------------------------------
# Workflow Nodes
# ---------------------------------------------------------------------------

def clarify_stage(node_input: Any) -> Event:
    """Stage 1: Requirement clarification (coding-clarify)."""
    return Event(
        output={"stage": "clarify", "result": node_input},
        actions=EventActions(route="to_specify"),
    )


def specify_stage(node_input: Any) -> Event:
    """Stage 2: Specification synthesis and artifact generation (coding-specify)."""
    data = node_input if isinstance(node_input, dict) else {}
    approved = data.get("approved")
    if approved is True:
        route = "approved"
    elif approved is False:
        route = "rejected"
    else:
        route = "awaiting_approval"

    return Event(
        output={"stage": "specify", "result": node_input},
        actions=EventActions(route=route),
    )


def plan_stage(node_input: Any) -> Event:
    """Stage 3: Multi-repo architecture planning and branch naming (coding-plan)."""
    data = node_input if isinstance(node_input, dict) else {}
    approved = data.get("approved")
    if approved is True:
        route = "approved"
    elif approved is False:
        route = "rejected"
    else:
        route = "awaiting_approval"

    return Event(
        output={"stage": "plan", "result": node_input},
        actions=EventActions(route=route),
    )


def develop_stage(node_input: Any) -> Event:
    """Stage 4: Isolated per-repo development (coding-develop)."""
    return Event(
        output={"stage": "develop", "result": node_input},
        actions=EventActions(route="to_review"),
    )


def review_stage(node_input: Any) -> Event:
    """Stage 5: Cross-repo consistency and spec validation (coding-review)."""
    data = node_input if isinstance(node_input, dict) else {}
    has_discrepancies = bool(data.get("discrepancies"))
    route = "discrepancy" if has_discrepancies else "approved"

    return Event(
        output={"stage": "review", "result": node_input},
        actions=EventActions(route=route),
    )


def merge_stage(node_input: Any) -> Event:
    """Stage 6: Branch merging or PR submission (coding-merge)."""
    return Event(
        output={"stage": "merge", "result": node_input},
        actions=EventActions(route="completed"),
    )


def create_coding_orchestrator_workflow() -> Workflow:
    """Instantiate the ADK Workflow graph for coding orchestration."""
    edges = [
        (START, clarify_stage),
        (clarify_stage, specify_stage),
        (specify_stage, {"approved": plan_stage, "rejected": clarify_stage}),
        (plan_stage, {"approved": develop_stage, "rejected": clarify_stage}),
        (develop_stage, review_stage),
        (review_stage, {"discrepancy": plan_stage, "approved": merge_stage}),
    ]

    return Workflow(
        name="coding_orchestrator",
        description=ORCHESTRATOR_DESCRIPTION,
        edges=edges,
    )
