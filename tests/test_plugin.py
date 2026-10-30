"""Tests for agentic-coding-plugin structure and scripts."""

from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent


def test_post_install_script_exists_and_executable():
    post_install = PLUGIN_ROOT / "scripts" / "post_install.sh"
    assert post_install.exists(), "scripts/post_install.sh must exist"
    assert post_install.stat().st_mode & 0o111, "scripts/post_install.sh must be executable"


def test_plugin_manifest_valid():
    import json
    manifest_file = PLUGIN_ROOT / "plugin.json"
    assert manifest_file.exists(), "plugin.json must exist"
    data = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert data.get("name") == "agentic-coding-plugin"
    assert data.get("license") == "MIT"


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
    assert "MIT License" in content


def test_skills_exist():
    skill_file = PLUGIN_ROOT / "skills" / "clean-code-reviewer" / "SKILL.md"
    assert skill_file.exists(), "clean-code-reviewer/SKILL.md must exist"


def test_rules_exist():
    rules_file = PLUGIN_ROOT / "rules" / "AGENTS.md"
    assert rules_file.exists(), "rules/AGENTS.md must exist"


def test_session_start_hook_deactivated():
    import json
    hooks_file = PLUGIN_ROOT / "hooks.json"
    assert hooks_file.exists(), "hooks.json must exist"
    data = json.loads(hooks_file.read_text(encoding="utf-8"))
    has_session_start = False
    for hook_name, hook_config in data.items():
        if "SessionStart" in hook_config:
            has_session_start = True
            assert hook_config.get("enabled") is False, f"Hook '{hook_name}' with SessionStart must have enabled: false"
    assert has_session_start, "SessionStart must be present and deactivated in hooks.json"


def test_canonical_agent_handles():
    """Verify that documentation and specifications use canonical @coding-* handles."""
    central_agent_md = PLUGIN_ROOT / "agents" / "agent.md"
    assert central_agent_md.exists()
    content = central_agent_md.read_text(encoding="utf-8")

    # Canonical handles must be present
    assert "@coding" in content
    assert "@coding-clarify" in content
    assert "@coding-specify" in content
    assert "@coding-plan" in content
    assert "@coding-develop" in content
    assert "@coding-review" in content
    assert "@coding-merge" in content
    assert "@coding-investigate" in content
    assert "@coding-monitor" in content
    assert "@coding-document" in content
    assert "@coding-research" in content

    # Legacy handles must not be present
    assert "`@investigate`" not in content
    assert "(`@investigate`)" not in content
    assert "`@monitoring`" not in content
    assert "(`@monitoring`)" not in content


def test_readme_companion_handles():
    """Verify README references canonical companion handles."""
    readme = PLUGIN_ROOT / "README.md"
    assert readme.exists()
    content = readme.read_text(encoding="utf-8")
    assert "@coding" in content
    assert "@coding-investigate" in content
    assert "@coding-monitor" in content
    assert "@coding-document" in content
    assert "@coding-research" in content

