"""Tests for self-contained prompt triage hook and Laya Router System 1 model."""

import asyncio
import json
import subprocess
import sys
from pathlib import Path
import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from hooks.prompt_triage import (
    HookContext,
    HookResult,
    PromptTriageHook,
    prompt_triage_pre_turn,
    session_start_triage,
    extract_prompt_text,
    clean_user_prompt,
    LayaTriageEngine,
    CONFIDENCE_THRESHOLD,
    TRIAGE_QUESTION,
    TRIAGE_RESPONSES,
)


def test_clean_user_prompt():
    # 1. XML wrapper tags and additional metadata
    raw1 = (
        "<USER_REQUEST>\nExplain this code\n</USER_REQUEST>\n"
        "<ADDITIONAL_METADATA>\nThe current local time is: 2026-10-26T10:55:12+01:00.\n</ADDITIONAL_METADATA>"
    )
    assert clean_user_prompt(raw1) == "Explain this code"

    # 2. Trailing concatenated file paths at end of prompt (with and without space)
    raw2 = (
        "<USER_REQUEST>\n"
        "Improve prompt_triage.py -> lower the threeshold to 0.4\n"
        "/Users/gpfister/Development/Projects/gpfister/agentic/gp-coding-plugin/hooks/register_subagents.py"
        "/Users/gpfister/Development/Projects/gpfister/agentic/gp-coding-plugin/hooks/prompt_triage.py\n"
        "</USER_REQUEST>\n"
        "<ADDITIONAL_METADATA>some metadata</ADDITIONAL_METADATA>"
    )
    assert clean_user_prompt(raw2) == "Improve prompt_triage.py -> lower the threeshold to 0.4"

    # 3. Plain user input without wrappers
    raw3 = "Please refactor the database connector"
    assert clean_user_prompt(raw3) == "Please refactor the database connector"


def test_extract_prompt_text():
    assert extract_prompt_text("simple string") == "simple string"
    assert extract_prompt_text(["part1", "part2"]) == "part1 part2"


def test_prompt_triage_hook_allow():
    async def _run():
        context = HookContext()
        context.set_state("invocation_num", 0)

        hook = PromptTriageHook(use_router=False)
        result = await hook.run(context, "How does this code work?")

        assert isinstance(result, HookResult)
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


def test_session_start_hook():
    async def _run():
        context = HookContext()
        await session_start_triage(context)
        assert context.get_state("triage_initialized") is True
        assert context.get_state("invocation_num") == 0

    asyncio.run(_run())


def test_triage_stage3_response1_inquiries_no_changes():
    """Response 1: one or more inquiries involving no changes -> respond directly, no code changes."""
    engine = LayaTriageEngine(use_router=False)
    result = engine.triage("Can you explain how this module works?", invocation_num=0)
    assert result.response_choice == "response 1"
    assert result.intent == "question"
    assert result.response_confidence >= CONFIDENCE_THRESHOLD
    assert len(result.inject_steps) > 0
    assert "systemMessage" in result.inject_steps[0]
    msg = result.inject_steps[0]["systemMessage"]["systemMessage"]
    assert "=== Prompt Triage Telemetry & Metadata ===" in msg
    assert "What is this prompt about ?" in msg
    assert "Do not make any changes" in msg


def test_triage_stage3_response2_code_change_request():
    """Response 2: one or more code change request -> invoke coding subagent using invoke_subagent."""
    engine = LayaTriageEngine(use_router=False)
    result = engine.triage("Please implement a new login endpoint with JWT auth", invocation_num=0)
    assert result.response_choice == "response 2"
    assert result.intent == "coding"
    assert result.response_confidence >= CONFIDENCE_THRESHOLD
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
    result = engine.triage("@monitoring watch the serial console /dev/ttyUSB0", invocation_num=0)
    assert result.response_choice == "response 3"
    assert result.intent == "monitoring"
    assert result.response_confidence >= CONFIDENCE_THRESHOLD
    assert len(result.inject_steps) > 0
    assert "systemMessage" in result.inject_steps[0]
    msg = result.inject_steps[0]["systemMessage"]["systemMessage"]
    assert "=== Prompt Triage Telemetry & Metadata ===" in msg
    assert "What is this prompt about ?" in msg
    assert "invoke_subagent" in msg
    assert "monitoring" in msg


def test_triage_stage3_response4_issue_investigation_request():
    """Response 4: one or more issue investigation request -> invoke coding-investigate using invoke_subagent."""
    engine = LayaTriageEngine(use_router=False)
    result = engine.triage("Please investigate why the checkout endpoint returns 500 error", invocation_num=0)
    assert result.response_choice == "response 4"
    assert result.intent == "investigation"
    assert result.response_confidence >= CONFIDENCE_THRESHOLD
    assert len(result.inject_steps) > 0
    assert "systemMessage" in result.inject_steps[0]
    msg = result.inject_steps[0]["systemMessage"]["systemMessage"]
    assert "=== Prompt Triage Telemetry & Metadata ===" in msg
    assert "What is this prompt about ?" in msg
    assert "invoke_subagent" in msg
    assert "coding-investigate" in msg


def test_triage_stage3_response5_mixed_request():
    """Response 5: mix of inquiries, coding requests, task monitoring and/or investigation -> reject prompt."""
    engine = LayaTriageEngine(use_router=False)
    result = engine.triage(
        "Explain how the server starts and also implement a new fix and monitor the logs",
        invocation_num=0,
    )
    assert result.response_choice == "response 5"
    assert result.intent == "mixed"
    assert result.response_confidence >= CONFIDENCE_THRESHOLD
    assert len(result.inject_steps) > 0
    assert "systemMessage" in result.inject_steps[0]
    msg = result.inject_steps[0]["systemMessage"]["systemMessage"]
    assert "=== Prompt Triage Telemetry & Metadata ===" in msg
    assert "What is this prompt about ?" in msg
    assert "cannot process a mix" in msg


def test_triage_stage3_ambiguous_low_confidence_triggers_ask_question():
    """Low confidence (< 0.40): instructs main agent to submit question to user via ask_question."""
    engine = LayaTriageEngine(use_router=False)
    result = engine.triage("maybe something about project files", invocation_num=0)
    assert result.requires_user_confirmation is True
    assert result.response_confidence < CONFIDENCE_THRESHOLD
    assert len(result.inject_steps) > 0
    assert "systemMessage" in result.inject_steps[0]
    inject_str = str(result.inject_steps[0])
    assert "=== Prompt Triage Telemetry & Metadata ===" in inject_str
    assert "ask_question" in inject_str
    assert "What is this prompt about ?" in inject_str
    assert "one or more inquiries involving no changes" in inject_str
    assert "one or more code change request" in inject_str
    assert "one or more task monitoring request" in inject_str
    assert "one or more issue investigation request" in inject_str
    assert "a mix of inquiries, code change requests, task monitoring and/or issue investigation request" in inject_str
    assert "coding-investigate" in inject_str
    assert "invoke_subagent" in inject_str


def test_triage_stage3_real_laya_router_prediction():
    """Test actual Laya Router with system1 model and choice question."""
    engine = LayaTriageEngine(use_router=True)
    if engine._router is None:
        pytest.skip("Laya Router not available in this environment")

    # Coding request
    choice2, conf2, probs2 = engine.evaluate_system1_triage("Implement a REST API endpoint for user registration")
    assert choice2 == "response 2"
    assert conf2 >= CONFIDENCE_THRESHOLD
    assert "response 2" in probs2

    # Issue investigation request
    choice4, conf4, probs4 = engine.evaluate_system1_triage("Please investigate why the database connection drops unexpectedly")
    assert choice4 == "response 4"
    assert conf4 >= CONFIDENCE_THRESHOLD
    assert "response 4" in probs4


def test_triage_hook_script_cli(tmp_path: Path):
    """Test running hooks/prompt_triage.py via subprocess using uv on invocationNum == 0."""
    input_payload = {
        "conversationId": "test-conv-001",
        "invocationNum": 0,
        "lastUserInput": "<USER_REQUEST>Can you review this code?</USER_REQUEST><ADDITIONAL_METADATA>time</ADDITIONAL_METADATA>",
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


def test_triage_hook_skips_when_invocation_num_greater_than_zero(tmp_path: Path):
    """Test that invocationNum > 0 returns empty injectSteps (skips triage on subsequent tool steps)."""
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
    assert output == {"injectSteps": []}
