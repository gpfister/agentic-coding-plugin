"""coding-clarify worker subagent.

Implements the requirement clarification loop based on Matt Pocock's /grill-me pattern.
Relentlessly interviews the user one question at a time, providing recommendations,
until all requirements, edge cases, and scope boundaries are crystal clear.
"""

from __future__ import annotations

from typing import Any, Optional
from google.antigravity import Agent, AgentBehavior, CapabilitiesConfig, LocalAgentConfig

from gp_coding.schemas import ClarificationSummary, clarification_to_markdown

CLARIFY_SYSTEM_PROMPT = """You are coding-clarify, an expert requirement interrogation agent inspired by Matt Pocock's /grill-me.

Your sole mission is to thoroughly interview the user about their requested feature or task until there is zero ambiguity.
You do NOT write implementation code or modify project files.

INTERVIEW PROTOCOL:
1. Always ask questions ONE AT A TIME using the ask_question tool.
2. For each question, provide:
   - Clear context on why this question matters.
   - Specific choices (options).
   - Your recommended option prefixed with '(Recommended)'.
   - Concise technical rationale for the recommendation.
3. If an answer can be deduced by inspecting the codebase (using read_file or directory listing), inspect the code yourself rather than asking the user.
4. Walk down each branch of the design tree, resolving dependencies and edge cases.
5. When all ambiguities are resolved and scope is firmly bounded:
   - Output the final result conforming to the ClarificationSummary JSON schema.
   - Present the summary in markdown format.
   - Signal that the workflow is ready to proceed to coding-specify.
"""

CLARIFY_MODEL = "gemini-3.8-flash"


def create_clarify_config(
    workspace_path: Optional[str] = None,
    conversation_id: Optional[str] = None,
) -> LocalAgentConfig:
    """Create LocalAgentConfig for coding-clarify worker subagent."""
    capabilities = CapabilitiesConfig(
        enable_subagents=False,
        agent_behavior=AgentBehavior.INTERACTIVE,
        enabled_tools=["ask_question", "view_file", "search_web"],
    )
    return LocalAgentConfig(
        system_instructions=CLARIFY_SYSTEM_PROMPT,
        capabilities=capabilities,
        model=CLARIFY_MODEL,
        response_schema=ClarificationSummary,
        workspaces=[workspace_path] if workspace_path else None,
        conversation_id=conversation_id,
    )


def create_clarify_agent(
    workspace_path: Optional[str] = None,
    conversation_id: Optional[str] = None,
) -> Agent:
    """Instantiate coding-clarify agent."""
    config = create_clarify_config(workspace_path, conversation_id)
    return Agent(config)
