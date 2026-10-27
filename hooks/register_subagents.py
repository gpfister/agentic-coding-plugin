#!/usr/bin/env python3
"""SessionStart Hook: Registers subagents and injects orchestration guidance.

Reads agent specifications from agentic-coding-plugin/agents/*.md and uses define_agent
to register all pipeline and monitoring agents, injecting session startup guidance,
permissions, and Antigravity interactive artifact approval (Approve/Reject) protocols into Antigravity.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = PLUGIN_ROOT / "agents"


def parse_agent_frontmatter(md_path: Path) -> dict[str, str]:
    """Extract YAML frontmatter name and description from a markdown file."""
    content = md_path.read_text(encoding="utf-8")
    fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    metadata = {}
    if fm_match:
        for line in fm_match.group(1).splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                metadata[key.strip()] = val.strip().strip('"').strip("'")
    if "name" not in metadata:
        metadata["name"] = md_path.stem
    return metadata


def define_agent(
    name: str,
    description: str,
    system_prompt: str,
    enable_write_tools: bool = True,
    enable_subagent_tools: bool = False,
    enable_mcp_tools: bool = True,
) -> dict[str, Any]:
    """Define a subagent registration specification for use with define_agent / define_subagent."""
    return {
        "name": name,
        "description": description,
        "system_prompt": system_prompt,
        "enable_write_tools": enable_write_tools,
        "enable_subagent_tools": enable_subagent_tools,
        "enable_mcp_tools": enable_mcp_tools,
    }


# Alias for define_subagent compatibility
define_subagent = define_agent


def register_agents() -> list[dict[str, Any]]:
    """Register coding, monitoring, investigator, and pipeline worker agents using define_agent."""
    registered: list[dict[str, Any]] = []
    if not AGENTS_DIR.exists():
        return registered

    for md_file in sorted(AGENTS_DIR.glob("*.md")):
        meta = parse_agent_frontmatter(md_file)
        name = meta.get("name", md_file.stem)
        desc = meta.get("description", "")
        content = md_file.read_text(encoding="utf-8")
        body = re.sub(r"^---\s*\n.*?\n---\s*\n?", "", content, flags=re.DOTALL).strip()

        # Coding orchestrator and standalone issue investigators require subagent tools
        # to invoke worker subagents or handoff remediation to the coding agent.
        is_orchestrator_or_investigator = name in ("coding", "coding-investigate", "coding-investigator", "coding-invetigator")
        enable_write = True
        enable_subagents = is_orchestrator_or_investigator

        agent_spec = define_agent(
            name=name,
            description=desc,
            system_prompt=body,
            enable_write_tools=enable_write,
            enable_subagent_tools=enable_subagents,
            enable_mcp_tools=True,
        )
        registered.append(agent_spec)

    return registered


def discover_agents() -> list[dict[str, str]]:
    """Scan agentic-coding-plugin/agents/ for all markdown agent definitions."""
    agents = []
    if not AGENTS_DIR.exists():
        return agents
    for md_file in sorted(AGENTS_DIR.glob("*.md")):
        meta = parse_agent_frontmatter(md_file)
        meta["file_path"] = str(md_file)
        agents.append(meta)
    return agents


def build_session_guidance(
    agents: list[dict[str, str]],
    registered_agents: list[dict[str, Any]] | None = None,
) -> str:
    """Construct system guidance describing available subagents, registered agents, and orchestration protocol."""
    lines = [
        "agentic-coding-plugin Subagent System Initialized:",
        "",
        "Available Subagents (defined in agentic-coding-plugin/agents/):",
    ]
    for agent in agents:
        name = agent.get("name", "")
        desc = agent.get("description", "")
        lines.append(f"- `@{name}` ({name}): {desc}")

    if registered_agents:
        lines.extend([
            "",
            "Registered Subagents (configured via define_agent):",
        ])
        for reg in registered_agents:
            r_name = reg.get("name", "")
            r_desc = reg.get("description", "")
            lines.append(f"- `@{r_name}`: {r_desc}")

    lines.extend([
        "",
        "Subagent Registration & Orchestration Protocol:",
        "1. **Agent Registration & Permissions**:",
        "   - The main agent must register `@coding`, `@coding-investigate`, and worker subagents using `define_subagent` (or `define_agent`) before spawning them to grant required tool privileges.",
        "   - `@coding`: Orchestrator requiring `enable_write_tools=True` and `enable_subagent_tools=True`.",
        "   - `@coding-investigate`: Standalone issue investigator requiring `enable_write_tools=True` and `enable_subagent_tools=True`.",
        "   - Worker Subagents (`@coding-clarify`, `@coding-specify`, `@coding-plan`, `@coding-develop`, `@coding-review`, `@coding-merge`, `@monitoring`): Require `enable_write_tools=True` so they can author artifacts, edit code, and manage branches directly.",
        "2. **Spawning Subagents**: Use `invoke_subagent` to spawn `@coding` (TypeName='coding'), `@monitoring` (TypeName='monitoring'), or `@coding-investigate` (TypeName='coding-investigate').",
        "3. **Sequential Phase Handoffs**: Coordinate the 6-stage lifecycle:",
        "   - `coding-clarify` -> `coding-specify` -> `coding-plan` -> `coding-develop` (parallel per repo) -> `coding-review` -> `coding-merge`.",
        "4. **Antigravity Interactive Artifact Approval Protocol (Approve / Reject UI)**:",
        "   - **Mandatory Approval Gates**: `specification.md` (Stage 2), `plan.md` (Stage 3), and `issue-assessment.md` (`coding-investigate`) require user approval via Antigravity's interactive modal before proceeding to subsequent stages.",
        "   - **Artifact Location**: Write the artifact directly to the session artifact directory: `<appDataDir>/brain/<conversation-id>/<artifact_name>.md` (e.g. `specification.md`, `plan.md`, or `issue-assessment.md`).",
        "   - **Artifact Metadata**: You MUST provide `ArtifactMetadata` with `RequestFeedback=True` and `UserFacing=True` (e.g. `write_file(Path=..., Content=..., Overwrite=True, ArtifactMetadata={\"RequestFeedback\": True, \"UserFacing\": True})`).",
        "   - **Turn Termination & Sole Tool Call Rule (CRITICAL)**: To trigger the interactive Approve / Reject modal in the Antigravity UI, `write_file(..., RequestFeedback=True)` MUST be the **sole and final tool call of that turn**.",
        "     * DO NOT batch secondary tool calls (such as updating session notes in Obsidian, running shell commands, or sending messages) in the same turn or after the artifact creation. Any secondary updates must be executed *before* calling `write_file(RequestFeedback=true)`, or deferred until *after* the user provides feedback.",
        "     * Immediately stop calling tools after creating the artifact to end your turn so Antigravity presents the interactive review buttons to the user.",
        "   - **Handling User Decisions**: When the user clicks the UI button, Antigravity injects:",
        "     * `[Approved] <artifact>.md`: Proceed immediately to the next stage (`coding-plan` after `specification.md`, `coding-develop` workers after `plan.md`, or ask correction confirmation after `issue-assessment.md`).",
        "     * `[Rejected] <artifact>.md` (with optional feedback comments): Route feedback back to `coding-clarify` or `coding-investigate` to adjust scope and re-synthesize.",
        "5. **Standalone Subagents**:",
        "   - `@monitoring`: Telemetry and stream surveillance worker watching logs, serial consoles, and container streams with anomaly pause gates.",
        "   - `@coding-investigate`: Standalone issue investigator diagnosing root causes across repositories, formulating solutions in `issue-assessment.md`, requesting user approval, confirming whether to start correction, and invoking `@coding` upon approval.",
        "6. **Background Awaiting & Resumption**: When subagents are running asynchronously or awaiting user feedback, do not poll in a loop; Antigravity automatically wakes up the orchestrator when updates or user inputs arrive. Forward user feedback to the subagent using `send_message`.",
        "7. **Informational Questions**: When prompt triage flags an inquiry involving no changes, answer directly without making code modifications ('Do not make any changes').",
    ])
    return "\n".join(lines)


def main():
    try:
        raw_input = sys.stdin.read()
        payload = json.loads(raw_input) if raw_input.strip() else {}
    except Exception:
        payload = {}

    agents = discover_agents()
    registered = register_agents()
    guidance = build_session_guidance(agents, registered)

    inject_steps = [
        {
            "systemMessage": {
                "systemMessage": guidance
            }
        }
    ]

    print(json.dumps({"injectSteps": inject_steps}))


if __name__ == "__main__":
    main()
