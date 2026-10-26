"""coding-monitoring standalone worker subagent (can be mentioned as @monitoring).

Continuously monitors application logs, serial console streams, or background process traces.
Detects error patterns and pauses to ask the user for remediation instructions.
Supports multiple concurrent instances identified by unique suffixes (e.g. coding-monitoring-serial).
"""

from __future__ import annotations

from typing import Any, Optional
from google.antigravity import Agent, AgentBehavior, CapabilitiesConfig, LocalAgentConfig

from gp_coding.schemas import MonitoringAlert, monitoring_alert_to_markdown

MONITORING_SYSTEM_PROMPT = """You are coding-monitoring, a dedicated telemetry and system surveillance subagent.

Your role:
1. Stream and inspect targeted logs, serial console outputs, or container traces.
2. Watch for errors, crashes, stack traces, warning anomalies, or specified regex patterns.
3. Upon discovering an error:
   - Immediately capture the error context and surrounding log snippet.
   - Formulate a structured MonitoringAlert JSON.
   - Pause monitoring and use ask_question to ask the user how they wish to intervene (e.g. Restart process, Ignore, Abort, Inspect code).
4. Resume or modify monitoring based on the user's decision.
"""

MONITORING_MODEL = "gemini-3.8-flash-lite"


def create_monitoring_config(
    monitor_id: str,
    target: str,
    workspace_path: Optional[str] = None,
    conversation_id: Optional[str] = None,
) -> LocalAgentConfig:
    """Create LocalAgentConfig for a coding-monitoring instance."""
    capabilities = CapabilitiesConfig(
        enable_subagents=False,
        agent_behavior=AgentBehavior.INTERACTIVE,
        enabled_tools=["run_command", "view_file", "schedule", "ask_question"],
    )
    instructions = f"{MONITORING_SYSTEM_PROMPT}\n\nAssigned Monitor ID: '{monitor_id}'\nTarget: '{target}'"
    return LocalAgentConfig(
        system_instructions=instructions,
        capabilities=capabilities,
        model=MONITORING_MODEL,
        response_schema=MonitoringAlert,
        workspaces=[workspace_path] if workspace_path else None,
        conversation_id=conversation_id,
    )


def create_monitoring_agent(
    monitor_id: str,
    target: str,
    workspace_path: Optional[str] = None,
    conversation_id: Optional[str] = None,
) -> Agent:
    """Instantiate coding-monitoring agent."""
    config = create_monitoring_config(monitor_id, target, workspace_path, conversation_id)
    return Agent(config)
