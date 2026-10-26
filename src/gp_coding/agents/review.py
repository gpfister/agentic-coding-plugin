"""coding-review worker subagent.

Aggregates and verifies results from all parallel coding-develop subagents.
Enforces cross-repo consistency, specification compliance, and absence of scope creep.
If discrepancies are found, re-triggers coding-plan. If valid, gates on user merge approval.
"""

from __future__ import annotations

from typing import Any, Optional
from google.antigravity import Agent, AgentBehavior, CapabilitiesConfig, LocalAgentConfig

from gp_coding.schemas import ReviewReport, review_report_to_markdown

REVIEW_SYSTEM_PROMPT = """You are coding-review, a lead code reviewer and quality assurance gatekeeper.

Your responsibilities:
1. Wait for and collect the DevelopReport from every parallel coding-develop subagent.
2. Cross-verify the changes across all repositories:
   - Ensure the implementation strictly matches the original SpecificationDocument.
   - Verify that changes only cover the requested scope (zero unrequested modifications or creep).
   - Ensure interfaces, protocol types, schemas, and API contracts are 100% consistent across repos.
   - Confirm all unit test suites and linters pass cleanly.
3. Formulate the ReviewReport:
   - If ANY discrepancy or defect is discovered:
     * Detail the exact discrepancies.
     * Route back to coding-plan to prepare a revised plan addressing the defects.
   - If ALL checks pass:
     * Request user authorization to proceed with merging the branches via coding-merge.
     * Wait in background until the user provides merge approval.
"""

REVIEW_MODEL = "gemini-3.8-pro"


def create_review_config(
    workspace_path: Optional[str] = None,
    conversation_id: Optional[str] = None,
) -> LocalAgentConfig:
    """Create LocalAgentConfig for coding-review worker subagent."""
    capabilities = CapabilitiesConfig(
        enable_subagents=False,
        agent_behavior=AgentBehavior.INTERACTIVE,
        enabled_tools=["view_file", "run_command", "ask_question"],
    )
    return LocalAgentConfig(
        system_instructions=REVIEW_SYSTEM_PROMPT,
        capabilities=capabilities,
        model=REVIEW_MODEL,
        response_schema=ReviewReport,
        workspaces=[workspace_path] if workspace_path else None,
        conversation_id=conversation_id,
    )


def create_review_agent(
    workspace_path: Optional[str] = None,
    conversation_id: Optional[str] = None,
) -> Agent:
    """Instantiate coding-review agent."""
    config = create_review_config(workspace_path, conversation_id)
    return Agent(config)
