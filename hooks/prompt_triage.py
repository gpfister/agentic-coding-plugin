#!/usr/bin/env python3
"""Prompt Triage Lifecycle Hook for Antigravity.

Refactored to use google-antigravity SDK style hooks (PreTurnHook, HookContext,
and HookResult) with Laya Router decision intelligence.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import warnings
from pathlib import Path

os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings("ignore")

# Ensure src/ is importable
PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PLUGIN_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from google.antigravity import types
from google.antigravity.hooks import (
    HookContext,
    PreTurnHook,
    OnSessionStartHook,
    pre_turn,
    on_session_start,
)

from gp_coding.hooks import (
    PromptTriageHook,
    prompt_triage_pre_turn,
    session_start_triage,
    extract_prompt_text,
)

__all__ = [
    "PromptTriageHook",
    "prompt_triage_pre_turn",
    "session_start_triage",
    "extract_prompt_text",
]


async def run_hook_async(payload: dict) -> list[dict]:
    """Execute PromptTriageHook within an Antigravity HookContext."""
    prompt = payload.get("lastUserInput", "")
    if not prompt:
        return []

    context = HookContext()
    context.set_state("invocation_num", payload.get("invocationNum", 1))
    context.set_state("conversation_id", payload.get("conversationId"))
    context.set_state("artifact_dir", payload.get("artifactDirectoryPath"))

    hook = PromptTriageHook(use_router=True)
    await hook.run(context, prompt)

    inject_steps = context.get_state("inject_steps", [])
    return inject_steps if isinstance(inject_steps, list) else []


def main():
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            json.dump({"injectSteps": []}, sys.stdout)
            return

        payload = json.loads(raw_input)
        inject_steps = asyncio.run(run_hook_async(payload))
        json.dump({"injectSteps": inject_steps}, sys.stdout)
    except Exception:
        # Hooks must never crash the parent agent execution loop
        json.dump({"injectSteps": []}, sys.stdout)


if __name__ == "__main__":
    main()
