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
        "coding-investigate",
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
    assert "coding-invetigator" not in agent_names, "coding-invetigator typo should be eliminated"
    assert "coding-investigator" not in agent_names, "coding-investigator should be merged into coding-investigate"


def test_parse_frontmatter():
    coding_md = PLUGIN_ROOT / "agents" / "coding" / "agent.md"
    assert coding_md.exists()
    meta = parse_agent_frontmatter(coding_md)
    assert meta.get("name") == "coding"
    assert "orchestrator" in meta.get("description", "").lower()

    investigator_md = PLUGIN_ROOT / "agents" / "coding-investigate" / "agent.md"
    assert investigator_md.exists()
    meta_inv = parse_agent_frontmatter(investigator_md)
    assert meta_inv.get("name") == "coding-investigate"
    assert "investigation" in meta_inv.get("description", "").lower()

    root_agent_md = PLUGIN_ROOT / "agents" / "agent.md"
    assert root_agent_md.exists()
    meta_root = parse_agent_frontmatter(root_agent_md)
    assert meta_root.get("name") == "agent"
    assert "workflow" in meta_root.get("description", "").lower()


def test_subagent_directory_layout():
    """Verify that each subagent directory contains only agent.md: agents/<agent>/agent.md."""
    expected_agents = [
        "coding",
        "coding-clarify",
        "coding-develop",
        "coding-investigate",
        "coding-merge",
        "coding-monitoring",
        "coding-plan",
        "coding-review",
        "coding-specify",
        "monitoring",
    ]
    for agent_name in expected_agents:
        agent_dir = PLUGIN_ROOT / "agents" / agent_name
        assert agent_dir.is_dir(), f"Expected directory {agent_dir} to exist"
        agent_file = agent_dir / "agent.md"
        assert agent_file.is_file(), f"Expected {agent_file} to be a regular file"
        # Assert only agent.md exists in the directory
        dir_files = [f.name for f in agent_dir.iterdir() if not f.name.startswith(".")]
        assert dir_files == ["agent.md"], f"Expected only ['agent.md'] in {agent_dir}, got {dir_files}"

    # Verify central workflow guide agents/agent.md
    central_agent_md = PLUGIN_ROOT / "agents" / "agent.md"
    assert central_agent_md.is_file(), "agents/agent.md must exist"
    content = central_agent_md.read_text(encoding="utf-8")
    assert "6-Stage Coding Workflow" in content
    assert "Subagent Registration" in content


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
    assert "coding-investigate" in reg_names

    coding = next(r for r in registered if r["name"] == "coding")
    assert coding["enable_subagent_tools"] is True
    assert coding["enable_write_tools"] is True
    assert "Coding Workflow Orchestrator" in coding["system_prompt"]

    monitoring = next(r for r in registered if r["name"] == "monitoring")
    assert monitoring["enable_write_tools"] is True
    assert "monitoring" in monitoring["system_prompt"].lower()

    # Standalone issue investigator requires write tools (for issue assessment) and subagent tools (to invoke coding orchestrator)
    inv = next(r for r in registered if r["name"] == "coding-investigate")
    assert inv["enable_write_tools"] is True
    assert inv["enable_subagent_tools"] is True
    assert "Issue Investigator" in inv["system_prompt"]

    # Subagents coding-specify and coding-plan must have write tools enabled to author artifacts
    specify = next(r for r in registered if r["name"] == "coding-specify")
    assert specify["enable_write_tools"] is True

    plan = next(r for r in registered if r["name"] == "coding-plan")
    assert plan["enable_write_tools"] is True


def test_build_session_guidance():
    agents = discover_agents()
    registered = register_agents()
    guidance = build_session_guidance(agents, registered)
    assert "@coding" in guidance
    assert "@monitoring" in guidance
    assert "@coding-investigate" in guidance
    assert "define_agent" in guidance or "define_subagent" in guidance
    assert "invoke_subagent" in guidance
    assert "coding-clarify" in guidance
    assert "specification.md" in guidance
    assert "plan.md" in guidance
    assert "issue-assessment.md" in guidance
    assert "RequestFeedback" in guidance
    assert "sole and final tool call" in guidance
    assert "[Approved]" in guidance
    assert "[Rejected]" in guidance


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
    assert "@coding-investigate" in sys_msg
    assert "RequestFeedback" in sys_msg
    assert "sole and final tool call" in sys_msg
