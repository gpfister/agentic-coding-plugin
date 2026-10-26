"""Tests for SessionStart hook: register_subagents.py."""

import json
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from hooks.register_subagents import (
    discover_agents,
    parse_agent_frontmatter,
    build_session_guidance,
    define_agent,
    register_agents,
)


def test_discover_agents():
    agents = discover_agents()
    agent_names = [a.get("name") for a in agents]
    expected_agents = [
        "coding",
        "coding-clarify",
        "coding-develop",
        "coding-merge",
        "coding-monitoring",
        "coding-plan",
        "coding-review",
        "coding-specify",
        "monitoring",
    ]
    for expected in expected_agents:
        assert expected in agent_names, f"Expected agent '{expected}' to be discovered in agents/"
    assert "coding-orchestrator" not in agent_names, "coding-orchestrator should be merged into coding"


def test_parse_frontmatter():
    coding_md = PLUGIN_ROOT / "agents" / "coding.md"
    assert coding_md.exists()
    meta = parse_agent_frontmatter(coding_md)
    assert meta.get("name") == "coding"
    assert "orchestrator" in meta.get("description", "").lower()


def test_define_agent():
    spec = define_agent(
        name="test-agent",
        description="A test agent",
        system_prompt="You are a test agent.",
        enable_write_tools=True,
        enable_subagent_tools=False,
        enable_mcp_tools=True,
    )
    assert spec["name"] == "test-agent"
    assert spec["description"] == "A test agent"
    assert spec["enable_write_tools"] is True
    assert spec["enable_subagent_tools"] is False


def test_register_agents_uses_define_agent():
    registered = register_agents()
    reg_names = [r["name"] for r in registered]
    assert "coding" in reg_names
    assert "monitoring" in reg_names

    coding = next(r for r in registered if r["name"] == "coding")
    assert coding["enable_subagent_tools"] is True
    assert coding["enable_write_tools"] is True
    assert "Coding Workflow Orchestrator" in coding["system_prompt"]

    monitoring = next(r for r in registered if r["name"] == "monitoring")
    assert monitoring["enable_write_tools"] is True
    assert "monitoring" in monitoring["system_prompt"].lower()


def test_build_session_guidance():
    agents = discover_agents()
    registered = register_agents()
    guidance = build_session_guidance(agents, registered)
    assert "@coding" in guidance
    assert "@monitoring" in guidance
    assert "define_agent" in guidance or "define_subagent" in guidance
    assert "invoke_subagent" in guidance
    assert "coding-clarify" in guidance


def test_register_subagents_cli():
    input_payload = {
        "conversationId": "session-test-001",
        "workspacePaths": [str(PLUGIN_ROOT)],
    }
    proc = subprocess.run(
        ["uv", "run", "hooks/register_subagents.py"],
        cwd=str(PLUGIN_ROOT),
        input=json.dumps(input_payload),
        text=True,
        capture_output=True,
    )
    assert proc.returncode == 0
    output = json.loads(proc.stdout)
    assert "injectSteps" in output
    assert len(output["injectSteps"]) > 0
    sys_msg = output["injectSteps"][0]["systemMessage"]["systemMessage"]
    assert "define_agent" in sys_msg or "define_subagent" in sys_msg
    assert "@coding" in sys_msg
    assert "@monitoring" in sys_msg
