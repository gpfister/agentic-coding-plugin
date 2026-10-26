"""coding-plan worker subagent.

Converts approved specifications into a multi-repo implementation plan artifact (plan.md).
Allocates tasks per repository, selects branch naming conventions (feature/*, task/*, bugfix/*),
and gates execution on user approval.
"""

from __future__ import annotations

from typing import Any, Optional
from google.antigravity import Agent, AgentBehavior, CapabilitiesConfig, LocalAgentConfig

from gp_coding.schemas import PlanDocument, plan_to_markdown

PLAN_SYSTEM_PROMPT = """You are coding-plan, a principal software architect subagent.

Your role:
1. Ingest the approved specification from coding-specify.
2. Break the implementation down per repository (identifying mono-repo vs multi-repo boundaries).
3. Determine appropriate git branch names for each repository strictly following:
   - feature/<name> for new capabilities
   - task/<name> for refactorings, chores, or maintenance
   - bugfix/<name> for bug corrections
4. Structure atomic execution steps, files to create/modify, and concrete verification commands conforming to PlanDocument.
5. Write the plan artifact as 'plan.md' in the session artifact directory with RequestFeedback=true.
6. Await user feedback in the background:
   - If the user APPROVES the artifact: transition the workflow to coding-develop.
   - If the user REJECTS the artifact: solicit missing details and route back to coding-clarify.
   - If the user sends a PROMPT or feedback: route back to coding-clarify to re-align requirements.
"""

PLAN_MODEL = "gemini-3.8-pro"


def create_plan_config(
    workspace_path: Optional[str] = None,
    conversation_id: Optional[str] = None,
) -> LocalAgentConfig:
    """Create LocalAgentConfig for coding-plan worker subagent."""
    capabilities = CapabilitiesConfig(
        enable_subagents=False,
        agent_behavior=AgentBehavior.INTERACTIVE,
        enabled_tools=["create_file", "edit_file", "view_file", "run_command", "ask_question"],
    )
    return LocalAgentConfig(
        system_instructions=PLAN_SYSTEM_PROMPT,
        capabilities=capabilities,
        model=PLAN_MODEL,
        response_schema=PlanDocument,
        workspaces=[workspace_path] if workspace_path else None,
        conversation_id=conversation_id,
    )


def create_plan_agent(
    workspace_path: Optional[str] = None,
    conversation_id: Optional[str] = None,
) -> Agent:
    """Instantiate coding-plan agent."""
    config = create_plan_config(workspace_path, conversation_id)
    return Agent(config)
