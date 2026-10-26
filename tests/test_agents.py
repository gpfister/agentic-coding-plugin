"""Tests for Antigravity subagent configurations and ADK workflow graph."""

from gp_coding.agents.clarify import create_clarify_config, CLARIFY_MODEL
from gp_coding.agents.specify import create_specify_config, SPECIFY_MODEL
from gp_coding.agents.plan import create_plan_config, PLAN_MODEL
from gp_coding.agents.develop import create_develop_config, DEVELOP_MODEL
from gp_coding.agents.review import create_review_config, REVIEW_MODEL
from gp_coding.agents.merge import create_merge_config, MERGE_MODEL
from gp_coding.agents.monitoring import create_monitoring_config, MONITORING_MODEL
from gp_coding.agents.orchestrator import (
    create_coding_orchestrator_workflow,
    clarify_stage,
    specify_stage,
    plan_stage,
    develop_stage,
    review_stage,
    merge_stage,
)
from gp_coding.schemas import (
    ClarificationSummary,
    SpecificationDocument,
    PlanDocument,
    DevelopReport,
    ReviewReport,
    MergeReport,
    MonitoringAlert,
)


def test_clarify_agent_config():
    config = create_clarify_config()
    assert config.model == "gemini-3.8-flash"
    assert "ClarificationSummary" in str(config.response_schema)
    assert "ask_question" in [t.value if hasattr(t, "value") else str(t) for t in config.capabilities.enabled_tools]
    assert "view_file" in [t.value if hasattr(t, "value") else str(t) for t in config.capabilities.enabled_tools]


def test_specify_agent_config():
    config = create_specify_config()
    assert config.model == "gemini-3.8-flash"
    assert "SpecificationDocument" in str(config.response_schema)
    assert "create_file" in [t.value if hasattr(t, "value") else str(t) for t in config.capabilities.enabled_tools]


def test_plan_agent_config():
    config = create_plan_config()
    assert config.model == "gemini-3.8-pro"
    assert "PlanDocument" in str(config.response_schema)
    assert "create_file" in [t.value if hasattr(t, "value") else str(t) for t in config.capabilities.enabled_tools]


def test_develop_agent_config():
    config = create_develop_config(repo_name="core-lib", repo_path="/path/to/core")
    assert config.model == "gemini-3.8-pro"
    assert "DevelopReport" in str(config.response_schema)
    assert config.workspaces == ["/path/to/core"]
    assert "core-lib" in config.system_instructions


def test_review_agent_config():
    config = create_review_config()
    assert config.model == "gemini-3.8-pro"
    assert "ReviewReport" in str(config.response_schema)
    assert "view_file" in [t.value if hasattr(t, "value") else str(t) for t in config.capabilities.enabled_tools]


def test_merge_agent_config():
    config = create_merge_config()
    assert config.model == "gemini-3.8-flash-lite"
    assert "MergeReport" in str(config.response_schema)
    assert "run_command" in [t.value if hasattr(t, "value") else str(t) for t in config.capabilities.enabled_tools]


def test_monitoring_agent_config():
    config = create_monitoring_config(monitor_id="mon-serial", target="/dev/ttyS0")
    assert config.model == "gemini-3.8-flash-lite"
    assert "MonitoringAlert" in str(config.response_schema)
    assert "mon-serial" in config.system_instructions


def test_coding_orchestrator_workflow_graph():
    wf = create_coding_orchestrator_workflow()
    assert wf.name == "coding_orchestrator"
    assert len(wf.edges) == 6


def test_orchestrator_stage_events():
    # Clarify
    ev_clarify = clarify_stage("user request")
    assert ev_clarify.actions.route == "to_specify"

    # Specify
    ev_spec_approved = specify_stage({"approved": True})
    assert ev_spec_approved.actions.route == "approved"
    ev_spec_rejected = specify_stage({"approved": False})
    assert ev_spec_rejected.actions.route == "rejected"

    # Plan
    ev_plan_approved = plan_stage({"approved": True})
    assert ev_plan_approved.actions.route == "approved"

    # Develop
    ev_develop = develop_stage({"status": "done"})
    assert ev_develop.actions.route == "to_review"

    # Review
    ev_review_clean = review_stage({"discrepancies": []})
    assert ev_review_clean.actions.route == "approved"
    ev_review_disc = review_stage({"discrepancies": ["Missing tests"]})
    assert ev_review_disc.actions.route == "discrepancy"

    # Merge
    ev_merge = merge_stage({"merged": True})
    assert ev_merge.actions.route == "completed"
