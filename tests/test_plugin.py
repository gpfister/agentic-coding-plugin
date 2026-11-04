"""Tests for agentic-coding-plugin structure, subagents, and specifications."""

import json
from pathlib import Path
import re

PLUGIN_ROOT = Path(__file__).resolve().parent.parent


def parse_frontmatter(md_path: Path) -> dict:
    content = md_path.read_text(encoding="utf-8")
    fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    metadata = {}
    if fm_match:
        current_list_key = None
        for line in fm_match.group(1).splitlines():
            line_str = line.strip()
            if not line_str or line_str.startswith("#"):
                continue
            if line_str.startswith("- ") and current_list_key:
                val = line_str[2:].strip().strip('"').strip("'")
                metadata[current_list_key].append(val)
            elif ":" in line:
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if not val:
                    metadata[key] = []
                    current_list_key = key
                else:
                    current_list_key = None
                    if val.lower() == "true":
                        metadata[key] = True
                    elif val.lower() == "false":
                        metadata[key] = False
                    else:
                        metadata[key] = val
    return metadata


def test_post_install_script_exists_and_executable():
    post_install = PLUGIN_ROOT / "scripts" / "post_install.sh"
    assert post_install.exists(), "scripts/post_install.sh must exist"
    assert post_install.stat().st_mode & 0o111, "scripts/post_install.sh must be executable"


def test_plugin_manifest_valid():
    manifest_file = PLUGIN_ROOT / "plugin.json"
    assert manifest_file.exists(), "plugin.json must exist"
    data = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert data.get("name") == "agentic-coding-plugin"
    assert data.get("version") == "0.1.0"
    assert data.get("license") == "MIT"
    assert "description" in data and len(data["description"]) > 0


def test_pyproject_valid():
    pyproject_file = PLUGIN_ROOT / "pyproject.toml"
    assert pyproject_file.exists(), "pyproject.toml must exist"
    content = pyproject_file.read_text(encoding="utf-8")
    assert 'name = "agentic-coding-plugin"' in content
    assert 'version = "0.1.0"' in content
    assert 'requires-python = ">=3.11"' in content
    assert "pytest>=8.0.0" in content


def test_license_exists_and_mit():
    license_file = PLUGIN_ROOT / "LICENSE"
    assert license_file.exists(), "LICENSE must exist"
    content = license_file.read_text(encoding="utf-8")
    assert "MIT License" in content
    assert "Greg PFISTER" in content


def test_contributing_exists():
    contrib_file = PLUGIN_ROOT / "CONTRIBUTING.md"
    assert contrib_file.exists(), "CONTRIBUTING.md must exist"
    content = contrib_file.read_text(encoding="utf-8")
    assert "Contributing to agentic-coding-plugin" in content
    assert "coding-deploy" in content
    assert "MIT License" in content


def test_skills_exist():
    reviewer_skill = PLUGIN_ROOT / "skills" / "clean-code-reviewer" / "SKILL.md"
    assert reviewer_skill.exists(), "clean-code-reviewer/SKILL.md must exist"
    reviewer_meta = parse_frontmatter(reviewer_skill)
    assert reviewer_meta.get("name") == "clean-code-reviewer"

    orchestrator_skill = PLUGIN_ROOT / "skills" / "coding-orchestrator" / "SKILL.md"
    assert orchestrator_skill.exists(), "coding-orchestrator/SKILL.md must exist"
    orchestrator_content = orchestrator_skill.read_text(encoding="utf-8")
    assert "coding-deploy" in orchestrator_content
    assert "7-stage" in orchestrator_content


def test_rules_exist():
    rules_file = PLUGIN_ROOT / "rules" / "AGENTS.md"
    assert rules_file.exists(), "rules/AGENTS.md must exist"
    content = rules_file.read_text(encoding="utf-8")
    assert "Coding Standards & Guidelines" in content
    assert "@coding-deploy" in content


def test_canonical_agent_handles():
    """Verify that documentation and specifications use canonical @coding-* handles including @coding-deploy."""
    central_agent_md = PLUGIN_ROOT / "agents" / "agent.md"
    assert central_agent_md.exists()
    content = central_agent_md.read_text(encoding="utf-8")

    expected_handles = [
        "@coding",
        "@coding-clarify",
        "@coding-specify",
        "@coding-plan",
        "@coding-develop",
        "@coding-deploy",
        "@coding-review",
        "@coding-merge",
        "@coding-investigate",
        "@coding-monitor",
        "@coding-document",
        "@coding-research",
    ]
    for handle in expected_handles:
        assert handle in content, f"Expected {handle} in agents/agent.md"


def test_readme_companion_handles():
    """Verify README references canonical handles including @coding-deploy."""
    readme = PLUGIN_ROOT / "README.md"
    assert readme.exists()
    content = readme.read_text(encoding="utf-8")
    assert "@coding" in content
    assert "@coding-develop" in content
    assert "@coding-deploy" in content
    assert "@coding-review" in content
    assert "@coding-merge" in content
    assert "7-stage" in content


def test_subagent_directory_layout():
    """Verify that each subagent directory exists and contains only agent.md."""
    expected_agents = [
        "coding",
        "coding-clarify",
        "coding-specify",
        "coding-plan",
        "coding-develop",
        "coding-deploy",
        "coding-review",
        "coding-merge",
    ]
    for agent_name in expected_agents:
        agent_dir = PLUGIN_ROOT / "agents" / agent_name
        assert agent_dir.is_dir(), f"Expected directory {agent_dir} to exist"
        agent_file = agent_dir / "agent.md"
        assert agent_file.is_file(), f"Expected {agent_file} to be a regular file"
        dir_files = [f.name for f in agent_dir.iterdir() if not f.name.startswith(".")]
        assert dir_files == ["agent.md"], f"Expected only ['agent.md'] in {agent_dir}, got {dir_files}"

    central_agent_md = PLUGIN_ROOT / "agents" / "agent.md"
    assert central_agent_md.is_file(), "agents/agent.md must exist"
    content = central_agent_md.read_text(encoding="utf-8")
    assert "7-Stage Coding Workflow" in content
    assert "coding-deploy" in content


def test_subagents_frontmatter_and_permissions():
    """Verify frontmatter configurations and permissions for all subagents."""
    deploy_md = PLUGIN_ROOT / "agents" / "coding-deploy" / "agent.md"
    assert deploy_md.exists()
    meta = parse_frontmatter(deploy_md)
    assert meta.get("name") == "coding-deploy"
    assert meta.get("enable_write_tools") is True
    assert meta.get("enable_subagent_tools") is True
    assert meta.get("enable_mcp_tools") is True
    tools = meta.get("tools", [])
    for required_tool in ["run_command", "read_file", "list_dir", "write_file", "edit_file", "ask_question", "send_message", "invoke_subagent"]:
        assert required_tool in tools, f"coding-deploy must have '{required_tool}' tool"

    coding_md = PLUGIN_ROOT / "agents" / "coding" / "agent.md"
    meta_coding = parse_frontmatter(coding_md)
    assert meta_coding.get("name") == "coding"
    assert meta_coding.get("enable_subagent_tools") is True
    assert meta_coding.get("enable_write_tools") is True


def test_coding_deploy_specifications():
    """Verify specific instructions in coding-deploy/agent.md."""
    deploy_md = PLUGIN_ROOT / "agents" / "coding-deploy" / "agent.md"
    content = deploy_md.read_text(encoding="utf-8")
    assert "Local Deployment Specialist" in content
    assert "Deployment Issue" in content
    assert "deployment-issue.md" in content
    assert "RequestFeedback" in content
    assert "ask_question" in content
    assert "coding-develop" in content
    assert "DeployReport" in content


def test_coding_plan_local_deployment_assessment():
    """Verify that coding-plan assesses local deployment requirements."""
    plan_md = PLUGIN_ROOT / "agents" / "coding-plan" / "agent.md"
    content = plan_md.read_text(encoding="utf-8")
    assert "Local Deployment Assessment" in content
    assert "coding-deploy" in content


def test_coding_merge_prerequisites():
    """Verify that coding-merge waits for coding-develop and coding-deploy."""
    merge_md = PLUGIN_ROOT / "agents" / "coding-merge" / "agent.md"
    content = merge_md.read_text(encoding="utf-8")
    assert "coding-develop" in content
    assert "coding-deploy" in content
