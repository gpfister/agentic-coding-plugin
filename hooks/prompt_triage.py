#!/usr/bin/env python3
"""Prompt Triage Lifecycle Hook for Antigravity.

Triages incoming user prompts using Laya Router System 1 model:
Asks: "What is this prompt about ?" with:
- response 1: one or more inquiries involving no changes
- response 2: one or more code change request
- response 3: one or more task monitoring request
- response 4: one or more issue investigation request
- response 5: a mix of inquiries, code change requests, task monitoring and/or issue investigation request

If one response has confidence >= 0.4, directly triggers the corresponding triage action:
- response 1: main agent responds directly to prompt (no changes directive)
- response 2: main agent invokes coding subagent using invoke_subagent
- response 3: main agent invokes monitoring subagent using invoke_subagent
- response 4: main agent invokes coding-investigate subagent using invoke_subagent
- response 5: main agent rejects prompt (cannot process mixed requests)

Otherwise (confidence < 0.4), instructs the main agent to ask the user via ask_question.
All triage instructions and Laya Router question metadata are passed via systemMessage.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.40

TRIAGE_QUESTION = "What is this prompt about ?"
TRIAGE_RESPONSES = {
    "response 1": "one or more inquiries involving no changes",
    "response 2": "one or more code change request",
    "response 3": "one or more task monitoring request",
    "response 4": "one or more issue investigation request",
    "response 5": "a mix of inquiries, code change requests, task monitoring and/or issue investigation request",
}

RESPONSE_TO_INTENT = {
    "response 1": "question",
    "response 2": "coding",
    "response 3": "monitoring",
    "response 4": "investigation",
    "response 5": "mixed",
}

INTENT_TO_RESPONSE = {
    "question": "response 1",
    "coding": "response 2",
    "monitoring": "response 3",
    "investigation": "response 4",
    "mixed": "response 5",
}


def clean_user_prompt(text: str) -> str:
    """Extract and sanitize only the actual user prompt from raw input.

    Strips Antigravity wrapper tags (<USER_REQUEST>, <ADDITIONAL_METADATA>, etc.)
    and trailing concatenated file paths.
    """
    if not isinstance(text, str):
        text = str(text)

    # 1. If <USER_REQUEST> is present, extract its content (last occurrence)
    user_requests = re.findall(r"<USER_REQUEST>(.*?)(?:</USER_REQUEST>|$)", text, flags=re.DOTALL)
    if user_requests:
        text = user_requests[-1]

    # 2. Strip <ADDITIONAL_METADATA>...</ADDITIONAL_METADATA> and other XML tags
    text = re.sub(r"<ADDITIONAL_METADATA>.*?(?:</ADDITIONAL_METADATA>|$)", "", text, flags=re.DOTALL)
    text = re.sub(r"<CONTEXT>.*?(?:</CONTEXT>|$)", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)

    # 3. Strip trailing concatenated file paths at end of prompt (with or without preceding space)
    # Matches patterns like /Users/.../file.py or /path/to/file.ext attached at the end
    text = re.sub(r"((?:\s*|(?<=[a-zA-Z0-9_]))/(?:[a-zA-Z0-9_\.\-]+/)+[a-zA-Z0-9_\.\-]+)+$", "", text)

    # 4. Normalize whitespace
    return " ".join(text.split()).strip()


class HookResult(BaseModel):
    """Result of a hook execution."""
    allow: bool = True
    message: Optional[str] = None


class HookContext:
    """Context state passed to lifecycle hooks."""

    def __init__(self, initial_state: Optional[dict[str, Any]] = None):
        self._state: dict[str, Any] = dict(initial_state) if initial_state else {}\

    def get_state(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def set_state(self, key: str, value: Any) -> None:
        self._state[key] = value

    def update_state(self, updates: dict[str, Any]) -> None:
        self._state.update(updates)


class TriageResult(BaseModel):
    """Result of Laya System 1 prompt triage."""
    stage_reached: int = Field(default=3, description="Evaluation stage reached")
    in_scope: bool = Field(default=True, description="Whether prompt is in session scope")
    scope_confidence: float = Field(default=1.0, description="Confidence of scope determination")
    response_choice: Optional[str] = Field(
        default=None,
        description="Selected response: response 1, response 2, response 3, response 4, or response 5",
    )
    response_confidence: float = Field(default=1.0, description="Confidence of selected response")
    response_probabilities: Dict[str, float] = Field(
        default_factory=dict,
        description="Probabilities across response candidates",
    )
    requires_user_confirmation: bool = Field(
        default=False,
        description="True if confidence < 0.40 requiring ask_question user selection",
    )
    intent: Optional[str] = Field(default=None, description="Semantic intent: question, coding, monitoring, investigation, or mixed")
    intent_confidence: float = Field(default=1.0, description="Confidence of intent classification")
    inject_steps: List[Dict[str, Any]] = Field(default_factory=list, description="Antigravity injectSteps payload")


class LayaTriageEngine:
    """Wrapper around Laya Router with heuristic fallback for System 1 prompt triage."""

    def __init__(self, use_router: bool = True):
        self._router = None
        if use_router:
            try:
                from laya import Router
                self._router = Router(preload=False)
            except Exception as e:
                logger.warning(f"Could not initialize Laya Router, using fallback: {e}")
                self._router = None

    def _predict_with_laya(self, text: str, questions: dict[str, Any]) -> Optional[dict[str, Any]]:
        if not self._router:
            return None
        try:
            return self._router.predict({"prompt": text}, questions)
        except Exception as e:
            logger.warning(f"Laya prediction failed: {e}")
            return None

    def evaluate_system1_triage(self, prompt: str) -> tuple[str, float, dict[str, float]]:
        """Triage prompt using Laya Router system1 model.

        Asks: 'What is this prompt about ?'
        with:
        - response 1: one or more inquiries involving no changes
        - response 2: one or more code change request
        - response 3: one or more task monitoring request
        - response 4: one or more issue investigation request
        - response 5: a mix of inquiries, code change requests, task monitoring and/or issue investigation request

        Returns (choice, confidence, probabilities).
        """
        questions = {
            "about": {
                "type": "choice",
                "instructions": TRIAGE_QUESTION,
                "criteria": TRIAGE_RESPONSES,
            }
        }
        res = self._predict_with_laya(prompt, questions)
        if res and "answers" in res and "about" in res["answers"]:
            ans = res["answers"]["about"]
            choice = ans.get("choice", "response 1")
            probs = ans.get("probabilities", {})
            conf = probs.get(choice, ans.get("answer_confidence", 0.0))
            return choice, conf, probs

        return self._heuristic_system1_triage(prompt)

    def _heuristic_system1_triage(self, prompt: str) -> tuple[str, float, dict[str, float]]:
        """Deterministic fallback when Laya Router is disabled or offline."""
        prompt_lower = prompt.lower()

        # Check monitoring keywords
        has_monitoring = any(
            w in prompt_lower
            for w in ["monitor", "watch log", "watch serial", "tail -f", "serial console", "log stream", "@monitoring"]
        )
        # Check investigation keywords
        has_investigation = any(
            w in prompt_lower
            for w in [
                "investigate", "investigation", "investigating", "invetigate", "invetigation",
                "diagnose", "root cause", "find the cause", "find cause", "troubleshoot",
                "coding-investigate", "coding-investigator", "coding-invetigator",
                "@coding-investigate", "@coding-investigator", "@coding-invetigator",
                "track down the bug", "track down the issue", "track down the root cause"
            ]
        )
        # Check coding keywords
        has_coding = any(
            w in prompt_lower
            for w in ["write", "create", "implement", "build", "refactor", "bugfix", "fix", "feature", "code change", "@coding"]
        )
        # Check inquiry / question keywords
        has_inquiry = any(
            w in prompt_lower
            for w in ["how", "what", "why", "explain", "review", "inquiry", "is there", "can you tell", "describe", "where"]
        )

        if has_investigation and not has_monitoring and not any(w in prompt_lower for w in ["implement", "create feature", "deploy", "merge"]):
            # Questions clarifying or investigating an issue (e.g. "investigate why X fails") are pure investigation
            has_inquiry = False

        # Check for mixed prompt
        mixed_count = sum([bool(has_monitoring), bool(has_coding), bool(has_inquiry), bool(has_investigation)])
        if mixed_count >= 2:
            return "response 5", 0.90, {
                "response 1": 0.02,
                "response 2": 0.03,
                "response 3": 0.03,
                "response 4": 0.02,
                "response 5": 0.90,
            }

        if has_investigation:
            return "response 4", 0.92, {
                "response 1": 0.02,
                "response 2": 0.02,
                "response 3": 0.02,
                "response 4": 0.92,
                "response 5": 0.02,
            }

        if has_monitoring:
            return "response 3", 0.92, {
                "response 1": 0.02,
                "response 2": 0.02,
                "response 3": 0.92,
                "response 4": 0.02,
                "response 5": 0.02,
            }

        if has_coding:
            return "response 2", 0.90, {
                "response 1": 0.03,
                "response 2": 0.90,
                "response 3": 0.03,
                "response 4": 0.02,
                "response 5": 0.02,
            }

        if has_inquiry:
            return "response 1", 0.88, {
                "response 1": 0.88,
                "response 2": 0.04,
                "response 3": 0.03,
                "response 4": 0.03,
                "response 5": 0.02,
            }

        # Ambiguous / default fallback -> low confidence (< 0.40) to present choice to user
        return "response 1", 0.30, {
            "response 1": 0.30,
            "response 2": 0.20,
            "response 3": 0.20,
            "response 4": 0.15,
            "response 5": 0.15,
        }

    def triage(
        self,
        prompt: str,
        invocation_num: int = 0,
        metadata: Optional[dict[str, Any]] = None,
    ) -> TriageResult:
        """Run System 1 prompt triage and format systemMessage with metadata."""
        choice, conf, probs = self.evaluate_system1_triage(prompt)
        intent = RESPONSE_TO_INTENT.get(choice, "question")

        # Build metadata text detailing the question and result submitted to Laya Router
        metadata_lines = [
            "=== Prompt Triage Telemetry & Metadata ===",
            f'- Question: "{TRIAGE_QUESTION}"',
            f'- Selected Response: {choice} (\"{TRIAGE_RESPONSES.get(choice, "")}\")',
            f"- Confidence: {conf:.4f}",
            "- Probability Distribution:",
        ]
        for r_key, r_desc in TRIAGE_RESPONSES.items():
            prob_val = probs.get(r_key, 0.0)
            metadata_lines.append(f'  * {r_key} (\"{r_desc}\"): {prob_val:.4f}')

        if metadata:
            metadata_lines.append("- Context Metadata:")
            for m_k, m_v in metadata.items():
                if m_v is not None and m_k != "lastUserInput":
                    metadata_lines.append(f"  * {m_k}: {m_v}")

        metadata_text = "\n".join(metadata_lines)

        inject_steps: list[dict[str, Any]] = []

        if conf < CONFIDENCE_THRESHOLD:
            # Low confidence (< 0.40): instruct main agent to ask user via ask_question
            options = [
                TRIAGE_RESPONSES["response 1"],
                TRIAGE_RESPONSES["response 2"],
                TRIAGE_RESPONSES["response 3"],
                TRIAGE_RESPONSES["response 4"],
                TRIAGE_RESPONSES["response 5"],
            ]
            ask_guidance = (
                f"{metadata_text}\n\n"
                f"Prompt Triage: Intent classification is ambiguous (confidence {conf:.2f} < {CONFIDENCE_THRESHOLD:.2f}).\n"
                "You MUST present the choice to the user by submitting the following question using the `ask_question` tool:\n"
                f'- Question: "{TRIAGE_QUESTION}"\n'
                "- Options:\n"
                f'  1. "{options[0]}"\n'
                f'  2. "{options[1]}"\n'
                f'  3. "{options[2]}"\n'
                f'  4. "{options[3]}"\n'
                f'  5. "{options[4]}"\n\n'
                "Execution rules based on user selection:\n"
                "- If response 1 ('one or more inquiries involving no changes') is selected: the main agent will respond to the prompt directly with no code changes.\n"
                "- If response 2 ('one or more code change request') is selected: the main agent will invoke the coding subagent using invoke_subagent(TypeName='coding', Role='Coding Workflow Orchestrator', Prompt=...).\n"
                "- If response 3 ('one or more task monitoring request') is selected: the main agent will invoke the monitoring subagent using invoke_subagent(TypeName='monitoring', Role='Telemetry Monitor', Prompt=...).\n"
                "- If response 4 ('one or more issue investigation request') is selected: the main agent will invoke the coding-investigate subagent using invoke_subagent(TypeName='coding-investigate', Role='Issue Investigator', Prompt=...).\n"
                "- If response 5 ('a mix of inquiries, code change requests, task monitoring and/or issue investigation request') is selected: the main agent will reject the prompt responding that it cannot process a mix of inquiries, coding requests, monitoring tasks, and/or investigation tasks."
            )
            inject_steps.append({
                "systemMessage": {
                    "systemMessage": ask_guidance
                }
            })
            return TriageResult(
                stage_reached=3,
                in_scope=True,
                response_choice=choice,
                response_confidence=conf,
                response_probabilities=probs,
                requires_user_confirmation=True,
                intent=intent,
                intent_confidence=conf,
                inject_steps=inject_steps,
            )

        # High confidence (>= CONFIDENCE_THRESHOLD): directly trigger the corresponding action
        if choice == "response 1":
            directive = (
                "Prompt Triage Directive: Response 1 identified (inquiries involving no changes). "
                "Respond directly to the prompt. Do not make any changes."
            )
        elif choice == "response 2":
            directive = (
                "Prompt Triage Directive: Response 2 identified (code change request). "
                "You must invoke the coding subagent (@coding) using invoke_subagent:\n"
                "invoke_subagent(TypeName='coding', Role='Coding Workflow Orchestrator', Prompt=...). "
                "Do not write or modify application code directly in the main agent turn."
            )
        elif choice == "response 3":
            directive = (
                "Prompt Triage Directive: Response 3 identified (task monitoring request). "
                "You must invoke the monitoring subagent (@monitoring) using invoke_subagent:\n"
                "invoke_subagent(TypeName='monitoring', Role='Telemetry Monitor', Prompt=...). "
                "Do not perform monitoring directly in the main agent turn."
            )
        elif choice == "response 4":
            directive = (
                "Prompt Triage Directive: Response 4 identified (issue investigation request). "
                "You must invoke the coding-investigate subagent (@coding-investigate) using invoke_subagent:\n"
                "invoke_subagent(TypeName='coding-investigate', Role='Issue Investigator', Prompt=...). "
                "Do not perform investigation directly in the main agent turn."
            )
        else:  # response 5
            directive = (
                "Prompt Triage Directive: Response 5 identified (mix of inquiries, code change requests, task monitoring and/or issue investigation requests). "
                "You must reject the prompt, responding to the user that you cannot process a mix of inquiries, coding requests, monitoring tasks, and/or investigation tasks. "
                "Ask the user to separate their requests into individual inquiries, coding tasks, monitoring tasks, or investigation tasks."
            )

        full_message = f"{metadata_text}\n\n{directive}"
        inject_steps.append({
            "systemMessage": {
                "systemMessage": full_message
            }
        })

        return TriageResult(
            stage_reached=3,
            in_scope=True,
            response_choice=choice,
            response_confidence=conf,
            response_probabilities=probs,
            requires_user_confirmation=False,
            intent=intent,
            intent_confidence=conf,
            inject_steps=inject_steps,
        )


def extract_prompt_text(data: Any) -> str:
    """Extract plain text string from prompt primitive, dict, or list."""
    if isinstance(data, str):
        return data
    if isinstance(data, list):
        parts: list[str] = []
        for item in data:
            if isinstance(item, str):
                parts.append(item)
            elif hasattr(item, "text") and getattr(item, "text"):
                parts.append(str(getattr(item, "text")))
            elif isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
            elif hasattr(item, "name") and getattr(item, "name"):
                parts.append(f"/{getattr(item, 'name')}")
            elif isinstance(item, dict) and "name" in item:
                parts.append(f"/{item['name']}")
        return " ".join(parts)
    if hasattr(data, "text") and getattr(data, "text"):
        return str(getattr(data, "text"))
    if isinstance(data, dict):
        if "text" in data:
            return str(data["text"])
        if "lastUserInput" in data:
            return str(data["lastUserInput"])
    return str(data)


class PromptTriageHook:
    """Prompt triage hook that triages user prompts via Laya Router."""

    def __init__(self, use_router: bool = True):
        self.engine = LayaTriageEngine(use_router=use_router)

    async def run(self, context: HookContext, data: Any) -> HookResult:
        prompt_text = clean_user_prompt(extract_prompt_text(data))
        if not prompt_text:
            return HookResult(allow=True, message="empty prompt")

        inv_num = context.get_state("invocation_num", 0)
        conv_id = context.get_state("conversation_id", None)
        artifact_dir = context.get_state("artifact_dir", None)

        metadata = {
            "conversation_id": conv_id,
            "invocation_num": inv_num,
            "artifact_dir": artifact_dir,
        }

        result: TriageResult = self.engine.triage(
            prompt=prompt_text,
            invocation_num=inv_num,
            metadata=metadata,
        )

        context.set_state("triage_result", result)
        context.set_state("inject_steps", result.inject_steps)
        context.set_state("triage_intent", result.intent)
        context.set_state("response_choice", result.response_choice)
        context.set_state("response_confidence", result.response_confidence)
        context.set_state("requires_user_confirmation", result.requires_user_confirmation)

        return HookResult(
            allow=True,
            message=result.response_choice or result.intent or "allowed",
        )


def pre_turn(fn: Any) -> Any:
    return fn


def on_session_start(fn: Any) -> Any:
    return fn


async def session_start_triage(context: HookContext) -> None:
    context.set_state("triage_initialized", True)
    context.set_state("invocation_num", 0)


async def prompt_triage_pre_turn(context: HookContext, data: Any) -> HookResult:
    hook = PromptTriageHook(use_router=True)
    return await hook.run(context, data)


async def run_hook_async(payload: dict) -> list[dict]:
    """Execute PromptTriageHook within a HookContext."""
    # Antigravity PreInvocation fires before every model invocation within a turn
    # (including after tool calls like ask_question, read_file, etc.).
    # Only triage the initial user prompt on invocationNum == 0.
    # Skip triage when invocationNum > 0 to avoid re-firing after tool steps.
    inv_num = payload.get("invocationNum", 0)
    if inv_num > 0:
        return []

    raw_prompt = payload.get("lastUserInput", "")
    if not raw_prompt:
        transcript_path = payload.get("transcriptPath", "")
        if transcript_path and os.path.exists(transcript_path):
            try:
                with open(transcript_path, "r", encoding="utf-8") as f:
                    for line in reversed(f.readlines()):
                        try:
                            step = json.loads(line)
                            if step.get("type") == "USER_INPUT" or step.get("source") == "USER_EXPLICIT":
                                raw_prompt = step.get("content", "")
                                if raw_prompt:
                                    break
                        except Exception:
                            continue
            except Exception:
                pass

    prompt = clean_user_prompt(extract_prompt_text(raw_prompt))
    if not prompt:
        return []

    context = HookContext()
    context.set_state("invocation_num", inv_num)
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
