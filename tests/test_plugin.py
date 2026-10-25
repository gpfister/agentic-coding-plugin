"""Tests for gp-coding-plugin structure and scripts."""

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
    assert data.get("name") == "gp-coding-plugin"


def test_skills_exist():
    skill_file = PLUGIN_ROOT / "skills" / "clean-code-reviewer" / "SKILL.md"
    assert skill_file.exists(), "clean-code-reviewer/SKILL.md must exist"


def test_rules_exist():
    rules_file = PLUGIN_ROOT / "rules" / "AGENTS.md"
    assert rules_file.exists(), "rules/AGENTS.md must exist"
