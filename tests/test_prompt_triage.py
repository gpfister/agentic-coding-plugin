"""Tests for self-contained prompt triage hook and Laya Router System 1 model."""

import asyncio
import json
import subprocess
import sys
from pathlib import Path
import pytest

from google.antigravity import types
from google.antigravity.hooks import HookContext

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from hooks.prompt_triage import (
    PromptTriageHook,
    prompt_triage_pre_turn,
    session_start_triage,
    extract_prompt_text,
    LayaTriageEngine,
    TRIAGE_QUESTION,
    TRIAGE_RESPONSES,
)


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
        assert result.message in ("response 1", "question")
        assert context.get_state("triage_intent") == "question"
        assert context.get_state("response_choice") == "response 1"
        inject_steps = context.get_state("inject_steps")
        assert len(inject_steps) > 0
        assert "systemMessage" in inject_steps[0]
        assert "ephemeralMessage" not in inject_steps[0]
        sys_msg = inject_steps[0]["systemMessage"]["systemMessage"]
        assert "What is this prompt about ?" in sys_msg
        assert "Prompt Triage Directive" in sys_msg
        assert "Do not make any changes" in sys_msg

    asyncio.run(_run())


def test_sdk_style_session_start_hook():
    async def _run():
        context = HookContext()
        await session_start_triage.run(context, None)
        assert context.get_state("triage_initialized") is True
        assert context.get_state("invocation_num") == 1

    asyncio.run(_run())


def test_triage_stage3_response1_inquiries_no_changes():
    """Response 1: one or more inquiries involving no changes -> respond directly, no code changes."""
    engine = LayaTriageEngine(use_router=False)
    result = engine.triage("Can you explain how this module works?", invocation_num=2)
    assert result.response_choice == "response 1"
    assert result.intent == "question"
    assert result.response_confidence >= 0.80
    assert len(result.inject_steps) > 0
    assert "systemMessage" in result.inject_steps[0]
    msg = result.inject_steps[0]["systemMessage"]["systemMessage"]
    assert "=== Prompt Triage Telemetry & Metadata ===" in msg
    assert "What is this prompt about ?" in msg
    assert "Do not make any changes" in msg


def test_triage_stage3_response2_code_change_request():
    """Response 2: one or more code change request -> invoke coding subagent using invoke_subagent."""
    engine = LayaTriageEngine(use_router=False)
    result = engine.triage("Please implement a new login endpoint with JWT auth", invocation_num=2)
    assert result.response_choice == "response 2"
    assert result.intent == "coding"
    assert result.response_confidence >= 0.80
    assert len(result.inject_steps) > 0
    assert "systemMessage" in result.inject_steps[0]
    msg = result.inject_steps[0]["systemMessage"]["systemMessage"]
    assert "=== Prompt Triage Telemetry & Metadata ===" in msg
    assert "What is this prompt about ?" in msg
    assert "invoke_subagent" in msg
    assert "coding" in msg


def test_triage_stage3_response3_task_monitoring_request():
    """Response 3: one or more task monitoring request -> invoke monitoring subagent using invoke_subagent."""
    engine = LayaTriageEngine(use_router=False)
    result = engine.triage("@monitoring watch the serial console /dev/ttyUSB0", invocation_num=2)
    assert result.response_choice == "response 3"
    assert result.intent == "monitoring"
    assert result.response_confidence >= 0.80
    assert len(result.inject_steps) > 0
    assert "systemMessage" in result.inject_steps[0]
    msg = result.inject_steps[0]["systemMessage"]["systemMessage"]
    assert "=== Prompt Triage Telemetry & Metadata ===" in msg
    assert "What is this prompt about ?" in msg
    assert "invoke_subagent" in msg
    assert "monitoring" in msg


def test_triage_stage3_response4_mixed_request():
    """Response 4: mix of inquiries, coding requests and/or task monitoring -> reject prompt."""
    engine = LayaTriageEngine(use_router=False)
    result = engine.triage(
        "Explain how the server starts and also implement a new fix and monitor the logs",
        invocation_num=2,
    )
    assert result.response_choice == "response 4"
    assert result.intent == "mixed"
    assert result.response_confidence >= 0.80
    assert len(result.inject_steps) > 0
    assert "systemMessage" in result.inject_steps[0]
    msg = result.inject_steps[0]["systemMessage"]["systemMessage"]
    assert "=== Prompt Triage Telemetry & Metadata ===" in msg
    assert "What is this prompt about ?" in msg
    assert "cannot process a mix" in msg


def test_triage_stage3_ambiguous_low_confidence_triggers_ask_question():
    """Low confidence (< 0.80): instructs main agent to submit question to user via ask_question."""
    engine = LayaTriageEngine(use_router=False)
    result = engine.triage("maybe something about project files", invocation_num=2)
    assert result.requires_user_confirmation is True
    assert result.response_confidence < 0.80
    assert len(result.inject_steps) > 0
    assert "systemMessage" in result.inject_steps[0]
    inject_str = str(result.inject_steps[0])
    assert "=== Prompt Triage Telemetry & Metadata ===" in inject_str
    assert "ask_question" in inject_str
    assert "What is this prompt about ?" in inject_str
    assert "one or more inquiries involving no changes" in inject_str
    assert "one or more code change request" in inject_str
    assert "one or more task monitoring request" in inject_str
    assert "a mix of inquiries, code change requests and/or task monitoring request" in inject_str
    assert "invoke_subagent" in inject_str


def test_triage_stage3_real_laya_router_prediction():
    """Test actual Laya Router with system1 model and choice question."""
    engine = LayaTriageEngine(use_router=True)
    if engine._router is None:
        pytest.skip("Laya Router not available in this environment")

    choice, conf, probs = engine.evaluate_system1_triage("Implement a REST API endpoint for user registration")
    assert choice == "response 2"
    assert conf > 0.5
    assert "response 2" in probs


def test_triage_hook_script_cli(tmp_path: Path):
    """Test running hooks/prompt_triage.py via subprocess using uv."""
    input_payload = {
        "conversationId": "test-conv-001",
        "invocationNum": 1,
        "lastUserInput": "Can you review this code?",
        "artifactDirectoryPath": str(tmp_path),
    }

    proc = subprocess.run(
        ["uv", "run", "hooks/prompt_triage.py"],
        cwd=str(PLUGIN_ROOT),
        input=json.dumps(input_payload),
        text=True,
        capture_output=True,
    )
    assert proc.returncode == 0
    output = json.loads(proc.stdout)
    assert "injectSteps" in output
    assert len(output["injectSteps"]) > 0
    step = output["injectSteps"][0]
    assert "systemMessage" in step
    assert "ephemeralMessage" not in step
    msg = step["systemMessage"]["systemMessage"]
    assert "What is this prompt about ?" in msg
    assert "Telemetry & Metadata" in msg
