"""coding-merge worker subagent.

Handles git integration, branch merging, or pull request creation.
Detects if remote origin is configured:
- If no remote: performs clean local fast-forward or merge commit into master.
- If remote exists: pushes branch and creates a pull request via GitHub CLI (gh), waiting for approval.
"""

from __future__ import annotations

from typing import Any, Optional
from google.antigravity import Agent, AgentBehavior, CapabilitiesConfig, LocalAgentConfig

from gp_coding.schemas import MergeReport, merge_report_to_markdown

MERGE_SYSTEM_PROMPT = """You are coding-merge, a release engineer subagent.

Your responsibilities:
1. Inspect git configuration in the target repository (git remote -v, git status).
2. Determine merge strategy:
   - If NO remote repository is configured:
     * Checkout master / main.
     * Merge the development branch locally.
     * Emit MergeReport with status 'merged'.
   - If a remote repository IS configured:
     * Push the branch to origin.
     * Create a Pull Request (using gh pr create or git push).
     * Set status to 'pr_created' and wait for PR review / approval.
3. Emit structured MergeReport JSON and summary markdown.
"""

MERGE_MODEL = "gemini-3.8-flash-lite"


def create_merge_config(
    workspace_path: Optional[str] = None,
    conversation_id: Optional[str] = None,
) -> LocalAgentConfig:
    """Create LocalAgentConfig for coding-merge worker subagent."""
    capabilities = CapabilitiesConfig(
        enable_subagents=False,
        agent_behavior=AgentBehavior.INTERACTIVE,
        enabled_tools=["run_command", "view_file", "ask_question"],
    )
    return LocalAgentConfig(
        system_instructions=MERGE_SYSTEM_PROMPT,
        capabilities=capabilities,
        model=MERGE_MODEL,
        response_schema=MergeReport,
        workspaces=[workspace_path] if workspace_path else None,
        conversation_id=conversation_id,
    )


def create_merge_agent(
    workspace_path: Optional[str] = None,
    conversation_id: Optional[str] = None,
) -> Agent:
    """Instantiate coding-merge agent."""
    config = create_merge_config(workspace_path, conversation_id)
    return Agent(config)
