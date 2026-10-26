"""gp_coding package: Antigravity coding companion subagents and workflow orchestration."""

from gp_coding.hooks import (
    PromptTriageHook,
    prompt_triage_pre_turn,
    session_start_triage,
)

__all__ = [
    "PromptTriageHook",
    "prompt_triage_pre_turn",
    "session_start_triage",
    "__version__",
]
