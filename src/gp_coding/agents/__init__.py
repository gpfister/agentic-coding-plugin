"""Subagent definitions and workflow orchestrator for gp-coding-plugin."""

from gp_coding.agents.clarify import create_clarify_agent, CLARIFY_SYSTEM_PROMPT
from gp_coding.agents.specify import create_specify_agent, SPECIFY_SYSTEM_PROMPT
from gp_coding.agents.plan import create_plan_agent, PLAN_SYSTEM_PROMPT
from gp_coding.agents.develop import create_develop_agent, DEVELOP_SYSTEM_PROMPT
from gp_coding.agents.review import create_review_agent, REVIEW_SYSTEM_PROMPT
from gp_coding.agents.merge import create_merge_agent, MERGE_SYSTEM_PROMPT
from gp_coding.agents.monitoring import create_monitoring_agent, MONITORING_SYSTEM_PROMPT
from gp_coding.agents.orchestrator import create_coding_orchestrator_workflow

__all__ = [
    "create_clarify_agent",
    "CLARIFY_SYSTEM_PROMPT",
    "create_specify_agent",
    "SPECIFY_SYSTEM_PROMPT",
    "create_plan_agent",
    "PLAN_SYSTEM_PROMPT",
    "create_develop_agent",
    "DEVELOP_SYSTEM_PROMPT",
    "create_review_agent",
    "REVIEW_SYSTEM_PROMPT",
    "create_merge_agent",
    "MERGE_SYSTEM_PROMPT",
    "create_monitoring_agent",
    "MONITORING_SYSTEM_PROMPT",
    "create_coding_orchestrator_workflow",
]
