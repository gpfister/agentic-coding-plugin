"""coding-specify worker subagent.

Consolidates clarified requirements into a formal specification artifact (specification.md).
Handles user approval, rejection, and mid-review feedback loops.
"""

from __future__ import annotations

from typing import Any, Optional
from google.antigravity import Agent, AgentBehavior, CapabilitiesConfig, LocalAgentConfig

from gp_coding.schemas import SpecificationDocument, specification_to_markdown

SPECIFY_SYSTEM_PROMPT = """You are coding-specify, a software specification architect subagent.

Your role:
1. Receive requirement clarifications from coding-clarify.
2. Synthesize them into an exhaustive, unambiguous specification adhering to the SpecificationDocument schema.
3. Write the specification artifact as 'specification.md' in the session artifact directory with RequestFeedback=true.
4. Convert and present the specification to the user using the markdown converter.
5. Await user feedback in the background:
   - If the user APPROVES the artifact: signal readiness to proceed to coding-plan.
   - If the user REJECTS the artifact: request additional details and route back to coding-clarify.
   - If the user provides extra PROMPTS or FEEDBACK before approving/rejecting: route the feedback to coding-clarify to update requirements.
"""

SPECIFY_MODEL = "gemini-3.8-flash"


def create_specify_config(
    workspace_path: Optional[str] = None,
    conversation_id: Optional[str] = None,
) -> LocalAgentConfig:
    """Create LocalAgentConfig for coding-specify worker subagent."""
    capabilities = CapabilitiesConfig(
        enable_subagents=False,
        agent_behavior=AgentBehavior.INTERACTIVE,
        enabled_tools=["create_file", "edit_file", "view_file", "ask_question"],
    )
    return LocalAgentConfig(
        system_instructions=SPECIFY_SYSTEM_PROMPT,
        capabilities=capabilities,
        model=SPECIFY_MODEL,
        response_schema=SpecificationDocument,
        workspaces=[workspace_path] if workspace_path else None,
        conversation_id=conversation_id,
    )


def create_specify_agent(
    workspace_path: Optional[str] = None,
    conversation_id: Optional[str] = None,
) -> Agent:
    """Instantiate coding-specify agent."""
    config = create_specify_config(workspace_path, conversation_id)
    return Agent(config)
