"""Tests for Laya Router prompt triage engine, Antigravity SDK style hooks, and CLI hook runner."""

import asyncio
import json
import subprocess
import sys
from pathlib import Path
import pytest

from google.antigravity import types
from google.antigravity.hooks import HookContext

from gp_coding.hooks import (
    PromptTriageHook,
    prompt_triage_pre_turn,
    session_start_triage,
    extract_prompt_text,
)
from gp_coding.state import WorkflowState, WorkflowStatus
from gp_coding.triage import LayaTriageEngine

PLUGIN_ROOT = Path(__file__).resolve().parent.parent


def test_extract_prompt_text():
    assert extract_prompt_text("simple string") == "simple string"
    assert extract_prompt_text(["part1", "part2"]) == "part1 part2"


def test_sdk_style_prompt_triage_hook_allow():
    async def _run():
        context = HookContext()
        context.set_state("invocation_num", 1)

        hook = PromptTriageHook(use_router=False)
        result = await hook.run(context, "How does this code work?")

        assert isinstance(result, types.HookResult)
        assert result.allow is True
        assert result.message == "question"
        assert context.get_state("triage_intent") == "question"
        inject_steps = context.get_state("inject_steps")
        assert any("Do not make any changes" in str(step) for step in inject_steps)

    asyncio.run(_run())


def test_sdk_style_prompt_triage_hook_deny_out_of_scope():
    async def _run():
        context = HookContext()
        context.set_state("invocation_num", 3)

        hook = PromptTriageHook(use_router=False)
        result = await hook.run(context, "What is the best recipe for baking bread?")

        assert isinstance(result, types.HookResult)
        assert result.allow is False
        assert "out of the scope" in result.message

    asyncio.run(_run())


def test_sdk_style_prompt_triage_waiting_agent_routing():
    async def _run():
        context = HookContext()
        context.set_state("invocation_num", 3)

        state = WorkflowState()
        state.start_workflow("wf-active-test")
        state.transition_to(
            status=WorkflowStatus.AWAITING_SPEC_APPROVAL,
            step="coding-specify",
            waiting_agent="coding-specify",
            waiting_conversation_id="conv-spec-555",
        )
        context.set_state("conversation_id", "test-conv-ctx")

        hook = PromptTriageHook(use_router=False)
        result = await hook.run(context, "@coding-specify this spec looks great, approved")

        assert result.allow is True
        inject_steps = context.get_state("inject_steps")
        assert any("coding-specify" in str(step) for step in inject_steps)

    asyncio.run(_run())


def test_sdk_style_session_start_hook():
    async def _run():
        context = HookContext()
        await session_start_triage.run(context, None)
        assert context.get_state("triage_initialized") is True
        assert context.get_state("invocation_num") == 1

    asyncio.run(_run())


def test_triage_stage1_session_start_always_in_scope():
    engine = LayaTriageEngine(use_router=False)
    in_scope, conf = engine.evaluate_scope("What should I eat for dinner?", invocation_num=1)
    assert in_scope is True
    assert conf == 1.0


def test_triage_stage1_out_of_scope_flagged():
    engine = LayaTriageEngine(use_router=False)
    in_scope, conf = engine.evaluate_scope("What is the recipe for chocolate cake?", invocation_num=2)
    assert in_scope is False
    assert conf >= 0.80


def test_triage_stage2_waiting_subagent_routed():
    engine = LayaTriageEngine(use_router=False)
    state = WorkflowState()
    state.start_workflow("wf-active")
    state.transition_to(
        status=WorkflowStatus.AWAITING_SPEC_APPROVAL,
        step="coding-specify",
        waiting_agent="coding-specify",
        waiting_conversation_id="conv-spec-999",
    )

    result = engine.triage("Looks good, approved!", invocation_num=3, state=state)
    assert result.stage_reached == 2
    assert result.routed_to_waiting_agent == "coding-specify"
    assert any("conv-spec-999" in str(step) for step in result.inject_steps)


def test_triage_stage3_question_intent():
    engine = LayaTriageEngine(use_router=False)
    result = engine.triage("Can you explain how this module works?", invocation_num=2)
    assert result.stage_reached == 3
    assert result.intent == "question"
    assert any("Do not make any changes" in str(step) for step in result.inject_steps)


def test_triage_stage3_coding_intent():
    engine = LayaTriageEngine(use_router=False)
    result = engine.triage("Please implement a new login endpoint with JWT auth", invocation_num=2)
    assert result.stage_reached == 3
    assert result.intent == "coding"
    assert any("coding-orchestrator" in str(step) for step in result.inject_steps)


def test_triage_stage3_monitoring_intent():
    engine = LayaTriageEngine(use_router=False)
    result = engine.triage("@monitoring watch the serial console /dev/ttyUSB0", invocation_num=2)
    assert result.stage_reached == 3
    assert result.intent == "monitoring"
    assert any("coding-monitoring" in str(step) for step in result.inject_steps)


def test_triage_hook_script_cli(tmp_path: Path):
    """Test running hooks/prompt_triage.py via subprocess CLI."""
    hook_script = PLUGIN_ROOT / "hooks" / "prompt_triage.py"
    input_payload = {
        "conversationId": "test-conv-001",
        "invocationNum": 1,
        "lastUserInput": "Can you review this code?",
        "artifactDirectoryPath": str(tmp_path),
    }

    proc = subprocess.run(
        [sys.executable, str(hook_script)],
        input=json.dumps(input_payload),
        text=True,
        capture_output=True,
    )
    assert proc.returncode == 0
    output = json.loads(proc.stdout)
    assert "injectSteps" in output
