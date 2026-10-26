"""Tests for gp_coding Pydantic schemas and Markdown converters."""

import pytest
from gp_coding.schemas import (
    ClarificationQuestion,
    ClarificationSummary,
    SpecificationDocument,
    PlanStep,
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
from gp_coding.utils.markdown import render_markdown


def test_clarification_schema_and_markdown():
    summary = ClarificationSummary(
        requirement_title="OAuth2 Integration",
        answered_questions={"Which provider?": "GitHub and Google"},
        confirmed_scope=["Auth endpoints", "JWT session tokens"],
        out_of_scope=["SAML 2.0"],
        ready_for_spec=True,
    )
    md = clarification_to_markdown(summary)
    assert "OAuth2 Integration" in md
    assert "Auth endpoints" in md
    assert "SAML 2.0" in md
    assert "GitHub and Google" in md
    assert "Ready for Specification" in md
    assert render_markdown(summary) == md


def test_specification_schema_and_markdown():
    spec = SpecificationDocument(
        title="Event Bus Module",
        summary="Asynchronous in-memory event bus",
        background="Needed for decoupling subagents",
        functional_requirements=["Publish events", "Subscribe with handlers"],
        non_functional_requirements=["Latency < 5ms"],
        acceptance_criteria=["Unit tests pass with >90% coverage"],
        approved=True,
    )
    md = specification_to_markdown(spec)
    assert "Event Bus Module" in md
    assert "Approved" in md
    assert "Publish events" in md
    assert "Acceptance Criteria" in md
    assert render_markdown(spec) == md


def test_plan_schema_and_markdown():
    step = PlanStep(
        step_number=1,
        repository="backend-api",
        description="Add /auth route",
        branch_name="feature/oauth2",
        files_to_create=["src/auth.py"],
        verification_commands=["pytest tests/test_auth.py"],
    )
    plan = PlanDocument(
        title="OAuth Implementation Plan",
        summary="Two-step implementation",
        branch_strategy={"backend-api": "feature/oauth2"},
        steps=[step],
        approved=None,
    )
    md = plan_to_markdown(plan)
    assert "OAuth Implementation Plan" in md
    assert "feature/oauth2" in md
    assert "src/auth.py" in md
    assert "Pending Approval" in md
    assert render_markdown(plan) == md


def test_develop_report_schema_and_markdown():
    report = DevelopReport(
        repository="backend-api",
        branch="feature/oauth2",
        files_created=["src/auth.py"],
        files_modified=["src/main.py"],
        tests_run=["pytest"],
        tests_passed=True,
        lint_passed=True,
        notes="All green",
    )
    md = develop_report_to_markdown(report)
    assert "backend-api" in md
    assert "feature/oauth2" in md
    assert "✅ Passed" in md
    assert render_markdown(report) == md


def test_review_report_schema_and_markdown():
    review = ReviewReport(
        summary="All multi-repo criteria met",
        reviewed_repositories=["backend-api", "frontend"],
        spec_compliance=True,
        consistency_across_repos=True,
        discrepancies=[],
        merge_approved=True,
    )
    md = review_report_to_markdown(review)
    assert "Review Assessment" in md
    assert "Ready for user merge authorization" in md
    assert render_markdown(review) == md

    review_with_disc = ReviewReport(
        summary="Found discrepancies",
        reviewed_repositories=["backend-api"],
        spec_compliance=False,
        consistency_across_repos=False,
        discrepancies=["Missing logout endpoint"],
        merge_approved=False,
    )
    md_disc = review_report_to_markdown(review_with_disc)
    assert "Missing logout endpoint" in md_disc
    assert "A revised plan will be triggered" in md_disc


def test_merge_report_schema_and_markdown():
    merge = MergeReport(
        repository="backend-api",
        source_branch="feature/oauth2",
        target_branch="master",
        merge_mode="local_merge",
        status="merged",
    )
    md = merge_report_to_markdown(merge)
    assert "backend-api" in md
    assert "local_merge" in md
    assert "merged" in md
    assert render_markdown(merge) == md


def test_monitoring_alert_schema_and_markdown():
    alert = MonitoringAlert(
        monitor_id="serial-01",
        target="/dev/ttyUSB0",
        timestamp="2026-10-25T18:00:00Z",
        severity="ERROR",
        error_message="Kernel panic: out of memory",
        log_snippet="[   12.345678] Kernel panic - not syncing: Out of memory",
        suggested_actions=["Reboot hardware", "Increase swap partition"],
    )
    md = monitoring_alert_to_markdown(alert)
    assert "serial-01" in md
    assert "Kernel panic" in md
    assert "Reboot hardware" in md
    assert render_markdown(alert) == md
