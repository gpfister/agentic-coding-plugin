#!/usr/bin/env python3
"""SessionStart Hook: Registers subagents and injects orchestration guidance.

Reads agent specifications from gp-coding-plugin/agents/*.md and injects
session startup instructions declaring @coding, @monitoring, and all worker subagents.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

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


def build_session_guidance(agents: list[dict[str, str]]) -> str:
    """Construct system guidance describing available subagents and orchestration protocol."""
    lines = [
        "gp-coding-plugin Subagent System Initialized:",
        "",
        "Available Subagents (defined in gp-coding-plugin/agents/):",
    ]
    for agent in agents:
        name = agent.get("name", "")
        desc = agent.get("description", "")
        lines.append(f"- `@{name}` ({name}): {desc}")

    lines.extend([
        "",
        "Subagent Orchestration Protocol:",
        "1. **Spawning Subagents**: Use `invoke_subagent` to spawn any subagent by its declared TypeName.",
        "   - `@coding` maps to `coding-orchestrator`",
        "   - `@monitoring` maps to `coding-monitoring`",
        "2. **Sequential Phase Handoffs**: When a subagent completes its task, the orchestrator/agent invokes the next stage's subagent using `invoke_subagent`.",
        "   - Workflow: `coding-clarify` -> `coding-specify` -> `coding-plan` -> `coding-develop` -> `coding-review` -> `coding-merge`.",
        "3. **Background Awaiting & Resumption**: When subagents await user input (`coding-specify` awaiting spec approval, `coding-plan` awaiting plan approval, `coding-review` awaiting merge approval), forward user feedback to the subagent using `send_message`.",
        "4. **Informational Questions**: When prompt triage flags a question, answer directly without making code modifications ('Do not make any changes').",
    ])
    return "\n".join(lines)


def main():
    try:
        raw_input = sys.stdin.read()
        payload = json.loads(raw_input) if raw_input.strip() else {}
    except Exception:
        payload = {}

    agents = discover_agents()
    guidance = build_session_guidance(agents)

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
