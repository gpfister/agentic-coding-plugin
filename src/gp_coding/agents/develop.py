"""coding-develop worker subagent.

Performs code implementation, unit testing, linting, documentation updates, and CI/CD adjustments.
Restricted to a single repository context. In multi-repo projects, multiple instances
execute in parallel with distinct repo identifiers (e.g. coding-develop-<repo>).
"""

from __future__ import annotations

from typing import Any, Optional
from google.antigravity import Agent, CapabilitiesConfig, LocalAgentConfig

from gp_coding.schemas import DevelopReport, develop_report_to_markdown

DEVELOP_SYSTEM_PROMPT = """You are coding-develop, a specialized software engineer subagent.

Your operational boundaries:
1. You work STRICTLY within your assigned single repository. Do not access or modify external repositories.
2. Ensure you check out or create the assigned branch (feature/*, task/*, bugfix/*) specified in the plan.
3. Perform all required development tasks:
   - Write clean, modular, maintainable production code.
   - Author thorough unit and integration tests.
   - Run tests and linters, verifying 100% clean passes.
   - Update repository documentation (README.md, docs, inline symbols).
   - Adjust CI/CD workflows if dependencies or test scripts change.
4. Conclude your execution by producing a structured DevelopReport JSON and formatting a markdown report for coding-review.
"""

DEVELOP_MODEL = "gemini-3.8-pro"


def create_develop_config(
    repo_name: str,
    repo_path: str,
    conversation_id: Optional[str] = None,
) -> LocalAgentConfig:
    """Create LocalAgentConfig for coding-develop worker scoped to a single repo."""
    capabilities = CapabilitiesConfig(
        enable_subagents=False,
        enabled_tools=["run_command", "create_file", "edit_file", "view_file"],
    )
    instructions = f"{DEVELOP_SYSTEM_PROMPT}\n\nAssigned Repository: '{repo_name}' at path: '{repo_path}'."
    return LocalAgentConfig(
        system_instructions=instructions,
        capabilities=capabilities,
        model=DEVELOP_MODEL,
        response_schema=DevelopReport,
        workspaces=[repo_path],
        conversation_id=conversation_id,
    )


def create_develop_agent(
    repo_name: str,
    repo_path: str,
    conversation_id: Optional[str] = None,
) -> Agent:
    """Instantiate coding-develop agent for a given repo."""
    config = create_develop_config(repo_name, repo_path, conversation_id)
    return Agent(config)
