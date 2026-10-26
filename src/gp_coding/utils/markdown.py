"""Markdown presentation helpers for gp-coding subagent outputs."""

from typing import Any
from gp_coding.schemas import (
    ClarificationSummary,
    SpecificationDocument,
    PlanDocument,
    DevelopReport,
    ReviewReport,
    MergeReport,
    MonitoringAlert,
    clarification_to_markdown,
    specification_to_markdown,
    plan_to_markdown,
    develop_report_to_markdown,
    review_report_to_markdown,
    merge_report_to_markdown,
    monitoring_alert_to_markdown,
)


def render_markdown(obj: Any) -> str:
    """Render any gp_coding structured model to user-facing Markdown."""
    if isinstance(obj, ClarificationSummary):
        return clarification_to_markdown(obj)
    if isinstance(obj, SpecificationDocument):
        return specification_to_markdown(obj)
    if isinstance(obj, PlanDocument):
        return plan_to_markdown(obj)
    if isinstance(obj, DevelopReport):
        return develop_report_to_markdown(obj)
    if isinstance(obj, ReviewReport):
        return review_report_to_markdown(obj)
    if isinstance(obj, MergeReport):
        return merge_report_to_markdown(obj)
    if isinstance(obj, MonitoringAlert):
        return monitoring_alert_to_markdown(obj)
    return str(obj)
