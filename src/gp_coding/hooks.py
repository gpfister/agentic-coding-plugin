"""Google Antigravity SDK style hooks for prompt triage and session lifecycle.

Implements PreTurnHook and decorators using google.antigravity.hooks.
"""

from __future__ import annotations

import logging
import os
import sys
import warnings
from typing import Any, Optional

os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings("ignore")

from google.antigravity import types
from google.antigravity.hooks import (
    HookContext,
    PreTurnHook,
    OnSessionStartHook,
    pre_turn,
    on_session_start,
)

from gp_coding.state import WorkflowState
from gp_coding.triage import LayaTriageEngine, TriageResult

logger = logging.getLogger(__name__)


def extract_prompt_text(data: types.Content) -> str:
    """Extract plain text string from SDK types.Content primitive or list."""
    if isinstance(data, str):
        return data
    if isinstance(data, list):
        parts: list[str] = []
        for item in data:
            if isinstance(item, str):
                parts.append(item)
            elif hasattr(item, "text") and getattr(item, "text"):
                parts.append(str(getattr(item, "text")))
            elif hasattr(item, "name") and getattr(item, "name"):
                parts.append(f"/{getattr(item, 'name')}")
        return " ".join(parts)
    if hasattr(data, "text") and getattr(data, "text"):
        return str(getattr(data, "text"))
    return str(data)


class PromptTriageHook(PreTurnHook):
    """Google Antigravity PreTurnHook that triages user prompts via Laya Router.

    Executes the 3-stage triage pipeline:
    1. Scope check (gates out-of-scope prompts)
    2. Waiting subagent routing (forwards input to waiting worker agents)
    3. Intent classification (Question with no-change directive, Coding, Monitoring)
    """

    def __init__(self, use_router: bool = True):
        self.engine = LayaTriageEngine(use_router=use_router)

    async def run(self, context: HookContext, data: types.Content) -> types.HookResult:
        prompt_text = extract_prompt_text(data).strip()
        if not prompt_text:
            return types.HookResult(allow=True, message="empty prompt")

        inv_num = context.get_state("invocation_num", 1)
        conv_id = context.get_state("conversation_id", None)
        artifact_dir = context.get_state("artifact_dir", None)

        state = WorkflowState.load(artifact_dir=artifact_dir, conversation_id=conv_id)
        result: TriageResult = self.engine.triage(
            prompt=prompt_text,
            invocation_num=inv_num,
            state=state,
        )

        # Store triage telemetry in HookContext
        context.set_state("triage_result", result)
        context.set_state("inject_steps", result.inject_steps)
        context.set_state("triage_intent", result.intent)
        context.set_state("routed_to_waiting_agent", result.routed_to_waiting_agent)

        # If prompt is determined out of scope with high confidence, deny turn with guidance
        if not result.in_scope and result.scope_confidence >= 0.80:
            return types.HookResult(
                allow=False,
                message=(
                    "Prompt appears out of the scope of this session. "
                    "Please ask the user whether they want to broaden the scope or stop."
                ),
            )

        return types.HookResult(
            allow=True,
            message=result.intent or "allowed",
        )


@pre_turn
async def prompt_triage_pre_turn(context: HookContext, data: types.Content) -> types.HookResult:
    """Decorator-based Antigravity PreTurnHook for prompt triage."""
    hook = PromptTriageHook(use_router=True)
    return await hook.run(context, data)


@on_session_start
async def session_start_triage(context: HookContext) -> None:
    """Antigravity OnSessionStartHook initializing triage state."""
    context.set_state("triage_initialized", True)
    context.set_state("invocation_num", 1)
