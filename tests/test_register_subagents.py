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
        "coding-orchestrator",
        "coding-plan",
        "coding-review",
        "coding-specify",
        "monitoring",
    ]
    for expected in expected_agents:
        assert expected in agent_names, f"Expected agent '{expected}' to be discovered in agents/"


def test_parse_frontmatter():
    orchestrator_md = PLUGIN_ROOT / "agents" / "coding-orchestrator.md"
    assert orchestrator_md.exists()
    meta = parse_agent_frontmatter(orchestrator_md)
    assert meta.get("name") == "coding-orchestrator"
    assert "orchestrator" in meta.get("description", "").lower()


def test_build_session_guidance():
    agents = discover_agents()
    guidance = build_session_guidance(agents)
    assert "@coding" in guidance
    assert "@monitoring" in guidance
    assert "invoke_subagent" in guidance
    assert "coding-clarify" in guidance


def test_register_subagents_cli():
    hook_script = PLUGIN_ROOT / "hooks" / "register_subagents.py"
    input_payload = {
        "conversationId": "session-test-001",
        "workspacePaths": [str(PLUGIN_ROOT)],
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
    assert len(output["injectSteps"]) > 0
    sys_msg = output["injectSteps"][0]["systemMessage"]["systemMessage"]
    assert "coding-orchestrator" in sys_msg
    assert "coding-monitoring" in sys_msg
