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
    tools = meta.get("tools", [])
    for required_tool in ["run_command", "read_file", "list_dir", "write_file", "ask_question", "send_message", "invoke_subagent"]:
        assert required_tool in tools, f"coding-deploy must have '{required_tool}' tool"
    assert "edit_file" not in tools, "coding-deploy must NOT declare 'edit_file'"

    coding_md = PLUGIN_ROOT / "agents" / "coding" / "agent.md"
    meta_coding = parse_frontmatter(coding_md)
    assert meta_coding.get("name") == "coding"
    coding_tools = meta_coding.get("tools", [])
    assert "invoke_subagent" in coding_tools, "coding must have 'invoke_subagent' tool"
    assert "write_file" in coding_tools, "coding must have 'write_file' tool"

    clarify_md = PLUGIN_ROOT / "agents" / "coding-clarify" / "agent.md"
    meta_clarify = parse_frontmatter(clarify_md)
    assert meta_clarify.get("name") == "coding-clarify"
    clarify_tools = meta_clarify.get("tools", [])
    assert "send_message" in clarify_tools, "coding-clarify must have 'send_message' tool"
    assert "ask_question" in clarify_tools, "coding-clarify must have 'ask_question' tool"

    review_md = PLUGIN_ROOT / "agents" / "coding-review" / "agent.md"
    meta_review = parse_frontmatter(review_md)
    assert meta_review.get("name") == "coding-review"
    review_tools = meta_review.get("tools", [])
    assert "send_message" in review_tools, "coding-review must have 'send_message' tool"
    assert "ask_question" in review_tools, "coding-review must have 'ask_question' tool"

    merge_md = PLUGIN_ROOT / "agents" / "coding-merge" / "agent.md"
    meta_merge = parse_frontmatter(merge_md)
    assert meta_merge.get("name") == "coding-merge"
    merge_tools = meta_merge.get("tools", [])
    assert "send_message" in merge_tools, "coding-merge must have 'send_message' tool"
    assert "ask_question" in merge_tools, "coding-merge must have 'ask_question' tool"


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


def test_question_relay_protocol_contracts():
    """Verify that Question Relay Protocol contracts and timeout mitigations exist across agents and skills."""
    files_to_check = [
        PLUGIN_ROOT / "agents" / "coding-clarify" / "agent.md",
        PLUGIN_ROOT / "agents" / "coding" / "agent.md",
        PLUGIN_ROOT / "agents" / "coding-deploy" / "agent.md",
        PLUGIN_ROOT / "agents" / "coding-review" / "agent.md",
        PLUGIN_ROOT / "agents" / "coding-merge" / "agent.md",
        PLUGIN_ROOT / "skills" / "coding-orchestrator" / "SKILL.md",
        PLUGIN_ROOT / "rules" / "AGENTS.md",
        PLUGIN_ROOT / "agents" / "agent.md",
    ]
    for file_path in files_to_check:
        assert file_path.exists(), f"{file_path} must exist"
        content = file_path.read_text(encoding="utf-8")
        assert "[QUESTION_RELAY_REQUEST]" in content, f"[QUESTION_RELAY_REQUEST] missing in {file_path.name}"
        assert "[QUESTION_RELAY_RESPONSE]" in content, f"[QUESTION_RELAY_RESPONSE] missing in {file_path.name}"

    # Verify timeout mitigation is documented
    orchestrator_skill = (PLUGIN_ROOT / "skills" / "coding-orchestrator" / "SKILL.md").read_text(encoding="utf-8")
    assert "timeout" in orchestrator_skill.lower()

    rules_content = (PLUGIN_ROOT / "rules" / "AGENTS.md").read_text(encoding="utf-8")
    assert "timeout" in rules_content.lower()

    agent_catalog = (PLUGIN_ROOT / "agents" / "agent.md").read_text(encoding="utf-8")
    assert "timeout" in agent_catalog.lower()


def test_artifact_approval_relay_protocol_contracts():
    """Verify that Artifact Approval Relay Protocol contracts exist across all specified files."""
    files_to_check = [
        PLUGIN_ROOT / "agents" / "coding-specify" / "agent.md",
        PLUGIN_ROOT / "agents" / "coding-plan" / "agent.md",
        PLUGIN_ROOT / "agents" / "coding-deploy" / "agent.md",
        PLUGIN_ROOT / "agents" / "coding" / "agent.md",
        PLUGIN_ROOT / "skills" / "coding-orchestrator" / "SKILL.md",
        PLUGIN_ROOT / "rules" / "AGENTS.md",
        PLUGIN_ROOT / "agents" / "agent.md",
    ]
    for file_path in files_to_check:
        assert file_path.exists(), f"{file_path} must exist"
        content = file_path.read_text(encoding="utf-8")
        assert "[ARTIFACT_APPROVAL_REQUEST]" in content, f"[ARTIFACT_APPROVAL_REQUEST] missing in {file_path.name}"
        assert "[ARTIFACT_APPROVAL_RESPONSE]" in content, f"[ARTIFACT_APPROVAL_RESPONSE] missing in {file_path.name}"

    # Verify orchestrator includes write_file in its tools
    coding_md = PLUGIN_ROOT / "agents" / "coding" / "agent.md"
    meta_coding = parse_frontmatter(coding_md)
    tools_coding = meta_coding.get("tools", [])
    assert "write_file" in tools_coding, "coding orchestrator must have 'write_file' tool"

    # Verify Section 7 exists in rules/AGENTS.md
    rules_content = (PLUGIN_ROOT / "rules" / "AGENTS.md").read_text(encoding="utf-8")
    assert "Artifact Approval Relay Protocol" in rules_content
    assert "Section 7" in rules_content or "## 7." in rules_content


def test_coding_merge_pr_waiting_and_sync():
    """Verify that coding-merge includes PR creation, waiting gate, compare fallback, and post-merge cleanup."""
    merge_md = PLUGIN_ROOT / "agents" / "coding-merge" / "agent.md"
    assert merge_md.exists()
    content = merge_md.read_text(encoding="utf-8")
    assert "gh pr create" in content
    assert "gh pr view" in content
    assert "[QUESTION_RELAY_REQUEST]" in content
    assert "[QUESTION_RELAY_RESPONSE]" in content
    assert "git checkout <base>" in content
    assert "git pull --ff-only" in content
    assert "git push origin --delete" in content
    assert "git branch -d" in content
    assert "git fetch --prune" in content
    assert "git branch --show-current" in content
    assert "compare" in content
    assert "github.com" in content
    assert "MergeReport" in content
    assert '"cleanup": true' in content


def test_coding_merge_complete_branch_cleanup_and_prune():
    """Verify that complete branch cleanup, prune, and base branch checkout are documented across all relevant files."""
    merge_md = PLUGIN_ROOT / "agents" / "coding-merge" / "agent.md"
    merge_content = merge_md.read_text(encoding="utf-8")
    assert "git push origin --delete <branch>" in merge_content
    assert "git fetch --prune origin" in merge_content
    assert "git branch -d <branch>" in merge_content
    assert "git branch -D <branch>" in merge_content
    assert "git branch --show-current" in merge_content
    assert '"cleanup": true' in merge_content
    assert '"deleted_branches"' in merge_content
    assert '"pruned": true' in merge_content

    skill_md = PLUGIN_ROOT / "skills" / "coding-orchestrator" / "SKILL.md"
    skill_content = skill_md.read_text(encoding="utf-8")
    assert "git push origin --delete" in skill_content
    assert "git fetch --prune origin" in skill_content
    assert "git branch -d" in skill_content
    assert "Post-Merge Base Synchronization & Complete Cleanup" in skill_content

    coding_agent_md = PLUGIN_ROOT / "agents" / "coding" / "agent.md"
    coding_agent_content = coding_agent_md.read_text(encoding="utf-8")
    assert "git push origin --delete" in coding_agent_content
    assert "git fetch --prune origin" in coding_agent_content
    assert "git branch -d" in coding_agent_content
    assert "complete cleanup/prune" in coding_agent_content.lower()

    agent_catalog_md = PLUGIN_ROOT / "agents" / "agent.md"
    agent_catalog_content = agent_catalog_md.read_text(encoding="utf-8")
    assert "git push origin --delete" in agent_catalog_content
    assert "git fetch --prune origin" in agent_catalog_content
    assert "git branch -d" in agent_catalog_content
    assert "Post-Merge Base Synchronization & Complete Cleanup" in agent_catalog_content
    assert "pruned: true" in agent_catalog_content


def test_coding_orchestrator_dual_mode_classification():
    """Verify @coding is classified as a Dual-Mode Orchestrator across rules, agent definitions, and skills."""
    files_to_check = [
        PLUGIN_ROOT / "rules" / "AGENTS.md",
        PLUGIN_ROOT / "agents" / "coding" / "agent.md",
        PLUGIN_ROOT / "skills" / "coding-orchestrator" / "SKILL.md",
        PLUGIN_ROOT / "agents" / "agent.md",
    ]
    for file_path in files_to_check:
        assert file_path.exists(), f"{file_path} must exist"
        content = file_path.read_text(encoding="utf-8")
        assert "Dual-Mode" in content, f"'Dual-Mode' missing in {file_path.name}"
        assert "Subagent Mode" in content, f"'Subagent Mode' missing in {file_path.name}"
        assert "Standalone Mode" in content, f"'Standalone Mode' missing in {file_path.name}"
        assert "caller_id" in content, f"'caller_id' missing in {file_path.name}"


def test_coding_orchestrator_multi_hop_relay_contracts():
    """Verify Multi-Hop Relay contracts and timeout mitigation instructions for @coding in Subagent Mode."""
    files_to_check = [
        PLUGIN_ROOT / "rules" / "AGENTS.md",
        PLUGIN_ROOT / "agents" / "coding" / "agent.md",
        PLUGIN_ROOT / "skills" / "coding-orchestrator" / "SKILL.md",
        PLUGIN_ROOT / "agents" / "agent.md",
    ]
    for file_path in files_to_check:
        assert file_path.exists(), f"{file_path} must exist"
        content = file_path.read_text(encoding="utf-8")
        assert "[ARTIFACT_APPROVAL_REQUEST]" in content, f"[ARTIFACT_APPROVAL_REQUEST] missing in {file_path.name}"
        assert "[ARTIFACT_APPROVAL_RESPONSE]" in content, f"[ARTIFACT_APPROVAL_RESPONSE] missing in {file_path.name}"
        assert "[QUESTION_RELAY_REQUEST]" in content, f"[QUESTION_RELAY_REQUEST] missing in {file_path.name}"
        assert "[QUESTION_RELAY_RESPONSE]" in content, f"[QUESTION_RELAY_RESPONSE] missing in {file_path.name}"
        assert "caller_id" in content, f"'caller_id' missing in {file_path.name}"
        assert "send_message" in content, f"'send_message' missing in {file_path.name}"

    # Specific negative constraints in Subagent Mode
    coding_agent = (PLUGIN_ROOT / "agents" / "coding" / "agent.md").read_text(encoding="utf-8")
    assert "MUST NOT" in coding_agent or "must not" in coding_agent.lower()
    assert "write_file(RequestFeedback=True)" in coding_agent

    coding_skill = (PLUGIN_ROOT / "skills" / "coding-orchestrator" / "SKILL.md").read_text(encoding="utf-8")
    assert "MUST NOT" in coding_skill or "must not" in coding_skill.lower()
    assert "write_file(RequestFeedback=True)" in coding_skill

    rules_content = (PLUGIN_ROOT / "rules" / "AGENTS.md").read_text(encoding="utf-8")
    assert "write_file(RequestFeedback=True)" in rules_content


def test_coding_orchestrator_anti_direct_coding_guardrails():
    """Verify that @coding has hard negative constraints against directly mutating source code, configs, Makefiles, or test suites."""
    files_to_check = [
        PLUGIN_ROOT / "agents" / "coding" / "agent.md",
        PLUGIN_ROOT / "skills" / "coding-orchestrator" / "SKILL.md",
    ]
    for file_path in files_to_check:
        assert file_path.exists(), f"{file_path} must exist"
        content = file_path.read_text(encoding="utf-8")
        assert "meta-orchestrator" in content.lower(), f"'meta-orchestrator' missing in {file_path.name}"
        assert "source code" in content.lower(), f"'source code' missing in {file_path.name}"
        assert "write_file" in content, f"'write_file' missing in {file_path.name}"
        assert "run_command" in content, f"'run_command' missing in {file_path.name}"
        assert "@coding-develop" in content, f"'@coding-develop' missing in {file_path.name}"
        assert "@coding-deploy" in content, f"'@coding-deploy' missing in {file_path.name}"
        assert "@coding-review" in content, f"'@coding-review' missing in {file_path.name}"
        assert "@coding-merge" in content, f"'@coding-merge' missing in {file_path.name}"

    # Verify tool privilege model in agents/agent.md documents constrained tool usage
    agent_catalog = (PLUGIN_ROOT / "agents" / "agent.md").read_text(encoding="utf-8")
    assert "write_file strictly" in agent_catalog or "write_file is strictly restricted" in agent_catalog
    assert "run_command" in agent_catalog


def test_coding_orchestrator_pre_clarified_fast_path():
    """Verify that @coding documents pre-clarified fast-path bypassing Phase 1 while strictly preserving Phase 2/3 gates."""
    files_to_check = [
        PLUGIN_ROOT / "agents" / "coding" / "agent.md",
        PLUGIN_ROOT / "skills" / "coding-orchestrator" / "SKILL.md",
        PLUGIN_ROOT / "agents" / "agent.md",
    ]
    for file_path in files_to_check:
        assert file_path.exists(), f"{file_path} must exist"
        content = file_path.read_text(encoding="utf-8")
        assert "Fast-Path" in content or "fast-path" in content, f"'Fast-Path' missing in {file_path.name}"
        assert "coding-clarify" in content, f"'coding-clarify' missing in {file_path.name}"
        assert "coding-specify" in content, f"'coding-specify' missing in {file_path.name}"
        assert "coding-plan" in content, f"'coding-plan' missing in {file_path.name}"


def test_coding_review_plan_audit_and_artifact():
    """Verify coding-review includes write_file, artifact-only guardrails, plan-vs-changes audit, and review-<slug>.md."""
    review_md = PLUGIN_ROOT / "agents" / "coding-review" / "agent.md"
    assert review_md.exists()

    meta = parse_frontmatter(review_md)
    tools = meta.get("tools", [])
    assert "write_file" in tools, "coding-review must include 'write_file' in tools"

    content = review_md.read_text(encoding="utf-8")
    assert "review-<slug>.md" in content
    assert "review-changes.md" in content
    assert "kebab-case" in content
    assert "[a-z0-9-]+" in content
    assert "git status" in content
    assert "git diff" in content
    assert "plan.md" in content
    assert "RequestFeedback=True" in content
    assert "[ARTIFACT_APPROVAL_REQUEST]" in content
    assert '"None"' in content
    assert "Artifact-Only" in content
    assert "MUST NEVER" in content

    required_sections = [
        "Plan vs. Actual Changes Audit",
        "Specification Compliance Check",
        "Cross-Repo Interface & Schema Compatibility",
        "Unit Tests & Linter Verification Results",
        "Local Deployment Health Status",
    ]
    for section in required_sections:
        assert section in content, f"Required review section '{section}' missing in coding-review/agent.md"


def test_coding_review_unplanned_changes_validation_gate():
    """Verify coding-review Unplanned Changes Validation Gate and separation from Merge Confirmation Gate."""
    review_md = PLUGIN_ROOT / "agents" / "coding-review" / "agent.md"
    content = review_md.read_text(encoding="utf-8")

    assert "Unplanned Changes Validation Gate" in content
    assert "[REVIEW_ARTIFACT]" in content
    assert content.index("[REVIEW_ARTIFACT]") < content.index('"Do you approve the changes ?"')
    assert "Do you approve the changes ?" in content
    assert "(Recommended) Yes" in content
    assert "No, revert all these changes" in content
    assert "[QUESTION_RELAY_REQUEST]" in content
    assert "ask_question" in content
    assert "ReviewReport" in content
    assert "coding-develop" in content
    assert "Separate Final Gate" in content or "Separate Merge Confirmation Gate" in content


def test_coding_orchestrator_review_plan_handoff_and_rework():
    """Verify orchestrator, skill, and catalog pass plan.md to coding-review and route revert/revision to coding-develop."""
    files_to_check = [
        PLUGIN_ROOT / "agents" / "coding" / "agent.md",
        PLUGIN_ROOT / "skills" / "coding-orchestrator" / "SKILL.md",
        PLUGIN_ROOT / "agents" / "agent.md",
    ]
    for file_path in files_to_check:
        assert file_path.exists(), f"{file_path} must exist"
        content = file_path.read_text(encoding="utf-8")
        assert "plan.md" in content, f"'plan.md' handoff missing in {file_path.name}"
        assert "review-<slug>.md" in content, f"'review-<slug>.md' missing in {file_path.name}"
        assert "Unplanned Changes Validation Gate" in content, f"'Unplanned Changes Validation Gate' missing in {file_path.name}"
        assert "No, revert all these changes" in content, f"'No, revert all these changes' missing in {file_path.name}"
        assert "ReviewReport" in content, f"'ReviewReport' missing in {file_path.name}"
        assert "@coding-develop" in content or "coding-develop" in content, f"'coding-develop' routing missing in {file_path.name}"

    for orchestrator_file in [
        PLUGIN_ROOT / "agents" / "coding" / "agent.md",
        PLUGIN_ROOT / "skills" / "coding-orchestrator" / "SKILL.md",
    ]:
        orch_content = orchestrator_file.read_text(encoding="utf-8")
        assert "[REVIEW_ARTIFACT]" in orch_content, f"[REVIEW_ARTIFACT] forwarding missing in {orchestrator_file.name}"


def test_worktree_isolation_and_exclusive_code_authority():
    """Verify worktree isolation lifecycle and exclusive coding-develop edit_file authority."""
    for agent_dir in (PLUGIN_ROOT / "agents").iterdir():
        if not agent_dir.is_dir():
            continue
        agent_md = agent_dir / "agent.md"
        if not agent_md.exists():
            continue
        meta = parse_frontmatter(agent_md)
        tools = meta.get("tools", [])
        if agent_dir.name == "coding-develop":
            assert "edit_file" in tools, "coding-develop must declare 'edit_file'"
        else:
            assert "edit_file" not in tools, f"{agent_dir.name} must NOT declare 'edit_file'"

    develop_content = (PLUGIN_ROOT / "agents" / "coding-develop" / "agent.md").read_text(encoding="utf-8")
    assert ".worktrees/" in develop_content
    assert "git worktree add" in develop_content
    assert "worktree_path" in develop_content
    assert "DevelopReport" in develop_content

    deploy_content = (PLUGIN_ROOT / "agents" / "coding-deploy" / "agent.md").read_text(encoding="utf-8")
    assert "worktree_path" in deploy_content
    assert "write_file` Restriction" in deploy_content or "deployment-issue" in deploy_content

    review_content = (PLUGIN_ROOT / "agents" / "coding-review" / "agent.md").read_text(encoding="utf-8")
    assert "worktree_path" in review_content

    merge_content = (PLUGIN_ROOT / "agents" / "coding-merge" / "agent.md").read_text(encoding="utf-8")
    assert "worktree remove" in merge_content
    assert "worktree prune" in merge_content

    for file_path in [
        PLUGIN_ROOT / "agents" / "coding" / "agent.md",
        PLUGIN_ROOT / "agents" / "agent.md",
        PLUGIN_ROOT / "skills" / "coding-orchestrator" / "SKILL.md",
        PLUGIN_ROOT / "rules" / "AGENTS.md",
    ]:
        content = file_path.read_text(encoding="utf-8")
        assert "worktree_path" in content, f"'worktree_path' missing in {file_path}"
        assert ".worktrees/" in content, f"'.worktrees/' missing in {file_path}"


def test_coding_orchestrator_ui_design_stage_and_change_request_loop():
    """Verify UI Design Stage placement, Dual-Mode DesignGate, Change-Request Loop, and AGENTS.md relay consistency."""
    skill_md = PLUGIN_ROOT / "skills" / "coding-orchestrator" / "SKILL.md"
    content = skill_md.read_text(encoding="utf-8")

    # Conflicting parallel/alongside wording must be removed
    assert "alongside `@coding-plan` and `@coding-develop`" not in content
    assert "alongside @coding-plan and @coding-develop" not in content

    # Section 3: Pre-Clarified Fast-Path checks design-spec.md and routes through DesignCheck
    assert "design-spec.md" in content
    assert "FastPathDesignCheck" in content

    # Section 4: Mermaid flowchart models DesignCheck, DesignGate, and Branch A/B rejection routing
    assert "DesignCheck" in content
    assert "InvokeDesign" in content
    assert "DesignGate" in content
    assert "DesignFeedbackEval" in content
    assert "DesignFeedbackEval -->|\"Functional / Scope Change<br/>(Branch A)\"| P2" in content
    assert "DesignFeedbackEval -->|\"Visual / Layout / Styling Only<br/>(Branch B)\"| InvokeDesign" in content

    # Section 5: Strict stage placement, Design Change-Request Loop, and downstream handoffs
    assert "strictly between `coding-specify` and `coding-plan`" in content
    assert "Design Change-Request Loop" in content
    assert "PenPot" in content
    assert "@coding-plan" in content
    assert "@coding-develop" in content

    # rules/AGENTS.md Sections 6 & 7 reference @coding-design
    rules_content = (PLUGIN_ROOT / "rules" / "AGENTS.md").read_text(encoding="utf-8")
    sec6 = rules_content.split("## 6. Question Relay Protocol")[1].split("## 7. Artifact Approval Relay Protocol")[0]
    sec7 = rules_content.split("## 7. Artifact Approval Relay Protocol")[1].split("## 8. Worktree Isolation")[0]
    assert "@coding-design" in sec6, "@coding-design must be listed in rules/AGENTS.md Section 6"
    assert "@coding-design" in sec7, "@coding-design must be listed in rules/AGENTS.md Section 7"


def test_coding_document_worktree_defer_pr_and_question_relay():
    """Verify @coding-document defer_pr coordination, Question Relay routing, and code-only @coding-merge scope."""
    files_to_check = [
        PLUGIN_ROOT / "agents" / "coding" / "agent.md",
        PLUGIN_ROOT / "skills" / "coding-orchestrator" / "SKILL.md",
        PLUGIN_ROOT / "rules" / "AGENTS.md",
    ]
    for file_path in files_to_check:
        content = file_path.read_text(encoding="utf-8")
        assert "defer_pr=true" in content, f"defer_pr=true missing in {file_path}"
        assert "defer_pr=false" in content, f"defer_pr=false missing in {file_path}"
        assert "@coding-document" in content, f"@coding-document missing in {file_path}"
        assert "docs/<slug>" in content, f"docs/<slug> missing in {file_path}"
        assert "*-obsidian/" in content, f"*-obsidian/ missing in {file_path}"
        assert "@coding-merge" in content and "code repositories exclusively" in content, (
            f"code-only @coding-merge scope missing in {file_path}"
        )

    coding_agent = (PLUGIN_ROOT / "agents" / "coding" / "agent.md").read_text(encoding="utf-8")
    assert "`@coding-clarify`, `@coding-deploy`, `@coding-review`, `@coding-merge`, `@coding-document`" in coding_agent

    orchestrator_skill = (PLUGIN_ROOT / "skills" / "coding-orchestrator" / "SKILL.md").read_text(encoding="utf-8")
    assert "`@coding-clarify`, `@coding-deploy`, `@coding-review`, `@coding-merge`, `@coding-document`" in orchestrator_skill

    rules_content = (PLUGIN_ROOT / "rules" / "AGENTS.md").read_text(encoding="utf-8")
    sec6 = rules_content.split("## 6. Question Relay Protocol")[1].split("## 7. Artifact Approval Relay Protocol")[0]
    assert "@coding-document" in sec6, "@coding-document must be listed in rules/AGENTS.md Section 6"



