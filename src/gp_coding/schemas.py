"""Rigid JSON output schemas and Markdown converters for gp-coding subagents.

Each subagent generates structured JSON validated against these schemas.
Markdown converters transform the structured data into human-readable presentations
and artifacts.
"""

from __future__ import annotations

from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 1. coding-clarify
# ---------------------------------------------------------------------------

class ClarificationQuestion(BaseModel):
    question: str = Field(description="The clarifying question to ask the user")
    options: list[str] = Field(default_factory=list, description="Available options for the user to choose from")
    recommended: Optional[str] = Field(default=None, description="Recommended answer prefixed with (Recommended)")
    reasoning: Optional[str] = Field(default=None, description="Rationale for the recommendation")


class ClarificationSummary(BaseModel):
    requirement_title: str = Field(description="Summary title of the requirement being clarified")
    answered_questions: dict[str, str] = Field(
        default_factory=dict, description="Mapping of question -> user answer"
    )
    confirmed_scope: list[str] = Field(default_factory=list, description="Explicitly in-scope items")
    out_of_scope: list[str] = Field(default_factory=list, description="Explicitly out-of-scope items")
    unresolved_questions: list[str] = Field(
        default_factory=list, description="Questions still awaiting clarification"
    )
    ready_for_spec: bool = Field(
        default=False, description="True when all ambiguities are resolved and ready for specification"
    )


def clarification_to_markdown(summary: ClarificationSummary) -> str:
    lines = [
        f"## Requirement Clarification: {summary.requirement_title}",
        "",
        "### Confirmed Scope",
    ]
    if summary.confirmed_scope:
        lines.extend([f"- {item}" for item in summary.confirmed_scope])
    else:
        lines.append("- *(None specified)*")

    lines.extend(["", "### Out of Scope"])
    if summary.out_of_scope:
        lines.extend([f"- {item}" for item in summary.out_of_scope])
    else:
        lines.append("- *(None specified)*")

    lines.extend(["", "### Resolved Questions & Answers"])
    if summary.answered_questions:
        for q, a in summary.answered_questions.items():
            lines.append(f"- **Q:** {q}\n  - **A:** {a}")
    else:
        lines.append("- *(No questions recorded)*")

    if summary.unresolved_questions:
        lines.extend(["", "### Pending Questions"])
        for q in summary.unresolved_questions:
            lines.append(f"- [ ] {q}")

    lines.extend(["", f"**Ready for Specification:** {'✅ Yes' if summary.ready_for_spec else '⏳ Pending answers'}"])
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 2. coding-specify
# ---------------------------------------------------------------------------

class SpecificationDocument(BaseModel):
    title: str = Field(description="Feature specification title")
    summary: str = Field(description="Executive summary of the feature")
    background: str = Field(description="Problem statement and motivation")
    functional_requirements: list[str] = Field(description="List of functional requirements")
    non_functional_requirements: list[str] = Field(default_factory=list, description="Quality and performance criteria")
    affected_repositories: list[str] = Field(default_factory=list, description="List of repositories involved")
    edge_cases: list[str] = Field(default_factory=list, description="Edge cases and mitigations")
    acceptance_criteria: list[str] = Field(description="Verifiable acceptance criteria")
    approved: Optional[bool] = Field(default=None, description="User approval status (None=pending, True=approved, False=rejected)")


def specification_to_markdown(spec: SpecificationDocument) -> str:
    lines = [
        f"# Specification: {spec.title}",
        "",
        f"**Approval Status:** {'✅ Approved' if spec.approved is True else ('❌ Rejected' if spec.approved is False else '⏳ Pending Approval')}",
        "",
        "## Summary",
        spec.summary,
        "",
        "## Background & Motivation",
        spec.background,
        "",
        "## Functional Requirements",
    ]
    lines.extend([f"- {req}" for req in spec.functional_requirements])

    if spec.non_functional_requirements:
        lines.extend(["", "## Non-Functional Requirements"])
        lines.extend([f"- {req}" for req in spec.non_functional_requirements])

    lines.extend(["", "## Affected Repositories"])
    if spec.affected_repositories:
        lines.extend([f"- `{repo}`" for repo in spec.affected_repositories])
    else:
        lines.append("- Current workspace repository")

    if spec.edge_cases:
        lines.extend(["", "## Edge Cases & Error Handling"])
        lines.extend([f"- {ec}" for ec in spec.edge_cases])

    lines.extend(["", "## Acceptance Criteria"])
    lines.extend([f"- [ ] {ac}" for ac in spec.acceptance_criteria])

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 3. coding-plan
# ---------------------------------------------------------------------------

class PlanStep(BaseModel):
    step_number: int = Field(description="Sequential step index")
    repository: str = Field(description="Repository where the step executes")
    description: str = Field(description="Action description")
    branch_name: str = Field(description="Branch name following feature/, task/, or bugfix/ convention")
    files_to_create: list[str] = Field(default_factory=list, description="Files to be created")
    files_to_modify: list[str] = Field(default_factory=list, description="Files to be edited")
    verification_commands: list[str] = Field(default_factory=list, description="Commands to verify changes")


class PlanDocument(BaseModel):
    title: str = Field(description="Implementation plan title")
    summary: str = Field(description="Plan summary and architecture overview")
    branch_strategy: dict[str, str] = Field(
        default_factory=dict, description="Mapping of repo_name -> branch name (feature/*, task/*, bugfix/*)"
    )
    steps: list[PlanStep] = Field(default_factory=list, description="Ordered implementation steps per repository")
    risks_and_mitigations: list[str] = Field(default_factory=list, description="Identified risks and mitigations")
    approved: Optional[bool] = Field(default=None, description="User approval status (None=pending, True=approved, False=rejected)")


def plan_to_markdown(plan: PlanDocument) -> str:
    lines = [
        f"# Implementation Plan: {plan.title}",
        "",
        f"**Approval Status:** {'✅ Approved' if plan.approved is True else ('❌ Rejected' if plan.approved is False else '⏳ Pending Approval')}",
        "",
        "## Overview",
        plan.summary,
        "",
        "## Branch Strategy",
    ]
    if plan.branch_strategy:
        for repo, branch in plan.branch_strategy.items():
            lines.append(f"- **{repo}**: `{branch}`")
    else:
        lines.append("- Standard feature branch")

    lines.extend(["", "## Execution Steps"])
    for step in plan.steps:
        lines.extend([
            f"### Step {step.step_number}: {step.description} (`{step.repository}`)",
            f"- **Branch:** `{step.branch_name}`",
        ])
        if step.files_to_create:
            lines.append(f"- **Create:** {', '.join(f'`{f}`' for f in step.files_to_create)}")
        if step.files_to_modify:
            lines.append(f"- **Modify:** {', '.join(f'`{f}`' for f in step.files_to_modify)}")
        if step.verification_commands:
            lines.append(f"- **Verify:** `{'; '.join(step.verification_commands)}`")
        lines.append("")

    if plan.risks_and_mitigations:
        lines.extend(["## Risks & Mitigations"])
        lines.extend([f"- {rm}" for rm in plan.risks_and_mitigations])

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 4. coding-develop
# ---------------------------------------------------------------------------

class DevelopReport(BaseModel):
    repository: str = Field(description="Target repository name")
    branch: str = Field(description="Active branch name")
    files_created: list[str] = Field(default_factory=list, description="List of created files")
    files_modified: list[str] = Field(default_factory=list, description="List of modified files")
    tests_run: list[str] = Field(default_factory=list, description="Executed test commands")
    tests_passed: bool = Field(description="Whether all unit tests succeeded")
    lint_passed: bool = Field(description="Whether linting and type checks passed")
    documentation_updated: bool = Field(default=True, description="Whether repo docs were updated")
    ci_cd_updated: bool = Field(default=False, description="Whether CI/CD pipelines were adjusted")
    notes: str = Field(default="", description="Development notes or observations")


def develop_report_to_markdown(report: DevelopReport) -> str:
    lines = [
        f"### Development Report: `{report.repository}`",
        f"- **Branch:** `{report.branch}`",
        f"- **Tests:** {'✅ Passed' if report.tests_passed else '❌ Failed'}",
        f"- **Linting:** {'✅ Clean' if report.lint_passed else '❌ Issues found'}",
        f"- **Docs Updated:** {'✅ Yes' if report.documentation_updated else '⚠️ No'}",
        f"- **CI/CD Updated:** {'✅ Yes' if report.ci_cd_updated else 'N/A'}",
        "",
        "#### Changes Applied",
    ]
    if report.files_created:
        lines.append(f"- **Created:** {', '.join(f'`{f}`' for f in report.files_created)}")
    if report.files_modified:
        lines.append(f"- **Modified:** {', '.join(f'`{f}`' for f in report.files_modified)}")
    if report.tests_run:
        lines.append(f"- **Verification Executed:** {', '.join(f'`{t}`' for t in report.tests_run)}")
    if report.notes:
        lines.extend(["", f"**Notes:** {report.notes}"])
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 5. coding-review
# ---------------------------------------------------------------------------

class ReviewReport(BaseModel):
    summary: str = Field(description="Executive review evaluation")
    reviewed_repositories: list[str] = Field(description="Repositories covered in this review")
    spec_compliance: bool = Field(description="True if changes strictly fulfill the original specification")
    consistency_across_repos: bool = Field(description="True if interfaces and dependencies are consistent across all repos")
    discrepancies: list[str] = Field(default_factory=list, description="Identified defects, scope breaches, or inconsistencies")
    merge_approved: bool = Field(description="True if changes are ready to merge (no discrepancies)")
    user_merge_requested: bool = Field(default=False, description="True if prompt is waiting for user merge approval")


def review_report_to_markdown(review: ReviewReport) -> str:
    lines = [
        "## Review Assessment",
        "",
        review.summary,
        "",
        f"- **Specification Compliance:** {'✅ Strict match' if review.spec_compliance else '❌ Discrepancies found'}",
        f"- **Cross-Repo Consistency:** {'✅ Verified' if review.consistency_across_repos else '❌ Inconsistencies detected'}",
        f"- **Reviewed Repositories:** {', '.join(f'`{r}`' for r in review.reviewed_repositories)}",
        "",
    ]
    if review.discrepancies:
        lines.extend([
            "### ⚠️ Discrepancies to Resolve",
            *(f"- {d}" for d in review.discrepancies),
            "",
            "> [!WARNING]",
            "> Changes cannot be merged yet. A revised plan will be triggered with `coding-plan`.",
            "",
        ])
    else:
        lines.extend([
            "> [!NOTE]",
            "> All verifications passed successfully. Ready for user merge authorization.",
            "",
            "**Action Required:** Please approve merge to proceed with `coding-merge`.",
        ])
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 6. coding-merge
# ---------------------------------------------------------------------------

class MergeReport(BaseModel):
    repository: str = Field(description="Repository merged")
    source_branch: str = Field(description="Development branch")
    target_branch: str = Field(default="master", description="Target base branch")
    merge_mode: Literal["local_merge", "pull_request"] = Field(description="local_merge if no remote, pull_request if remote exists")
    pr_url: Optional[str] = Field(default=None, description="URL of created Pull Request if applicable")
    status: Literal["merged", "pr_created", "waiting_approval", "failed"] = Field(description="Resulting status")
    notes: str = Field(default="", description="Additional merge details")


def merge_report_to_markdown(report: MergeReport) -> str:
    lines = [
        f"### Merge Status: `{report.repository}`",
        f"- **Source Branch:** `{report.source_branch}`",
        f"- **Target Branch:** `{report.target_branch}`",
        f"- **Mode:** `{report.merge_mode}`",
        f"- **Status:** `{report.status}`",
    ]
    if report.pr_url:
        lines.append(f"- **Pull Request:** [{report.pr_url}]({report.pr_url})")
    if report.notes:
        lines.append(f"- **Notes:** {report.notes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 7. coding-monitoring
# ---------------------------------------------------------------------------

class MonitoringAlert(BaseModel):
    monitor_id: str = Field(description="Unique identifier for the monitoring worker instance")
    target: str = Field(description="Stream target being monitored (e.g. app log path, serial console port)")
    timestamp: str = Field(description="Timestamp of detection")
    severity: Literal["INFO", "WARNING", "ERROR", "CRITICAL"] = Field(description="Severity level")
    error_message: str = Field(description="Detected error header or exception summary")
    log_snippet: str = Field(description="Contextual log or serial trace snippet")
    suggested_actions: list[str] = Field(default_factory=list, description="Recommended remediation actions")
    awaiting_user_decision: bool = Field(default=True, description="Whether monitoring paused waiting for user input")


def monitoring_alert_to_markdown(alert: MonitoringAlert) -> str:
    lines = [
        f"## 🚨 Monitoring Alert [{alert.severity}]: `{alert.monitor_id}`",
        f"**Target:** `{alert.target}` | **Time:** `{alert.timestamp}`",
        "",
        f"**Detected Error:** {alert.error_message}",
        "",
        "```text",
        alert.log_snippet.strip(),
        "```",
        "",
    ]
    if alert.suggested_actions:
        lines.append("### Suggested Next Actions:")
        lines.extend([f"- {action}" for action in alert.suggested_actions])
        lines.append("")

    if alert.awaiting_user_decision:
        lines.extend([
            "> [!IMPORTANT]",
            "> Monitoring paused for user intervention. How would you like to proceed?",
        ])
    return "\n".join(lines)
