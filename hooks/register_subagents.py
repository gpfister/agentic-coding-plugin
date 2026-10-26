#!/usr/bin/env python3
"""SessionStart Hook: Registers subagents and injects orchestration guidance.

Reads agent specifications from gp-coding-plugin/agents/*.md and uses define_agent
to register @coding and @monitoring agents, injecting session startup guidance into Antigravity.
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
    """Register coding and monitoring agents using define_agent."""
    registered: list[dict[str, Any]] = []

    # Register coding agent
    coding_md = AGENTS_DIR / "coding.md"
    if coding_md.exists():
        content = coding_md.read_text(encoding="utf-8")
        meta = parse_agent_frontmatter(coding_md)
        body = re.sub(r"^---\s*\n.*?\n---\s*\n?", "", content, flags=re.DOTALL).strip()
        coding_agent = define_agent(
            name="coding",
            description=meta.get(
                "description",
                "Coding Workflow Orchestrator coordinating the 6-stage software development lifecycle.",
            ),
            system_prompt=body,
            enable_write_tools=True,
            enable_subagent_tools=True,
            enable_mcp_tools=True,
        )
        registered.append(coding_agent)

    # Register monitoring agent
    monitoring_md = AGENTS_DIR / "monitoring.md"
    if not monitoring_md.exists():
        monitoring_md = AGENTS_DIR / "coding-monitoring.md"
    if monitoring_md.exists():
        content = monitoring_md.read_text(encoding="utf-8")
        meta = parse_agent_frontmatter(monitoring_md)
        body = re.sub(r"^---\s*\n.*?\n---\s*\n?", "", content, flags=re.DOTALL).strip()
        monitoring_agent = define_agent(
            name="monitoring",
            description=meta.get(
                "description",
                "Telemetry and stream surveillance worker watching logs, serial consoles, and container streams with anomaly pause gates.",
            ),
            system_prompt=body,
            enable_write_tools=True,
            enable_subagent_tools=False,
            enable_mcp_tools=True,
        )
        registered.append(monitoring_agent)

    return registered


def discover_agents() -> list[dict[str, str]]:
    """Scan gp-coding-plugin/agents/ for all markdown agent definitions."""
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
        "gp-coding-plugin Subagent System Initialized:",
        "",
        "Available Subagents (defined in gp-coding-plugin/agents/):",
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
        "1. **Agent Registration**: The main agent must register `@coding` and `@monitoring` using `define_subagent` (or `define_agent`) before invocation if not already active.",
        "   - `@coding`: Coordinates the 6-stage lifecycle (`coding-clarify` -> `coding-specify` -> `coding-plan` -> `coding-develop` -> `coding-review` -> `coding-merge`).",
        "   - `@monitoring`: Telemetry monitor for continuous log / serial stream surveillance.",
        "2. **Spawning Subagents**: Use `invoke_subagent` to spawn `@coding` (TypeName='coding') or `@monitoring` (TypeName='monitoring').",
        "3. **Sequential Phase Handoffs**: When a subagent completes its task, the orchestrator/agent invokes the next stage's subagent using `invoke_subagent`.",
        "   - Workflow: `coding-clarify` -> `coding-specify` -> `coding-plan` -> `coding-develop` -> `coding-review` -> `coding-merge`.",
        "4. **Background Awaiting & Resumption**: When subagents await user input (`coding-specify` awaiting spec approval, `coding-plan` awaiting plan approval, `coding-review` awaiting merge approval), forward user feedback to the subagent using `send_message`.",
        "5. **Informational Questions**: When prompt triage flags an inquiry involving no changes, answer directly without making code modifications ('Do not make any changes').",
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
