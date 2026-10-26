"""Prompt triage hook engine using Laya Router.

Implements the three-stage prompt evaluation pipeline:
1. Session Scope Check (noul decision, threshold >= 0.80)
2. Waiting Subagent Routing (choice decision, threshold >= 0.80)
3. Intent Classification: Question, Coding Request, Monitoring Request
   (choice decision, threshold >= 0.80 or user confirmation)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from gp_coding.state import WorkflowState, WorkflowStatus

logger = logging.getLogger(__name__)


class TriageResult(BaseModel):
    stage_reached: int = Field(description="Last evaluation stage reached (1, 2, or 3)")
    in_scope: bool = Field(default=True, description="Whether prompt is in session scope")
    scope_confidence: float = Field(default=1.0, description="Confidence of scope determination")
    routed_to_waiting_agent: Optional[str] = Field(default=None, description="Waiting agent name if routed")
    intent: Optional[str] = Field(default=None, description="Identified intent: question, coding, or monitoring")
    intent_confidence: float = Field(default=1.0, description="Confidence of intent classification")
    inject_steps: List[Dict[str, Any]] = Field(default_factory=list, description="Antigravity injectSteps payload")


class LayaTriageEngine:
    """Wrapper around Laya Router with heuristic fallback."""

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

    def evaluate_scope(self, prompt: str, invocation_num: int) -> tuple[bool, float]:
        """Stage 1: Evaluate if prompt is related to session scope.
        Returns (in_scope, confidence).
        """
        # Session just started: no analysis needed per spec
        if invocation_num <= 1:
            return True, 1.0

        questions = {
            "is_in_scope": {
                "type": "noul",
                "instructions": (
                    "Is the user's prompt related to software engineering, programming, coding, "
                    "system monitoring, or software architecture within this technical workspace session?"
                ),
            }
        }
        res = self._predict_with_laya(prompt, questions)
        if res and "answers" in res and "is_in_scope" in res["answers"]:
            ans = res["answers"]["is_in_scope"]
            prob = ans.get("probability", 1.0)
            conf = ans.get("confidence", prob)
            in_scope = prob >= 0.5
            return in_scope, conf

        # Deterministic fallback
        prompt_lower = prompt.lower()
        off_topic_words = ["weather", "recipe", "poem", "sports", "dinner", "vacation"]
        if any(w in prompt_lower for w in off_topic_words) and not any(
            code_w in prompt_lower for code_w in ["code", "script", "file", "build", "api"]
        ):
            return False, 0.95
        return True, 0.95

    def evaluate_waiting_agent_match(self, prompt: str, waiting_agent: str) -> tuple[bool, float]:
        """Stage 2: Check if prompt corresponds to the subagent awaiting user input."""
        questions = {
            "matches_waiting_subagent": {
                "type": "choice",
                "instructions": (
                    f"Does this user prompt address or provide input for the subagent '{waiting_agent}', "
                    "such as approving, rejecting, clarifying, or modifying the plan, specification, or merge?"
                ),
                "criteria": {
                    "matches": "User is approving, rejecting, giving feedback, or discussing the artifact/waiting step.",
                    "unrelated": "User is asking an entirely different question or requesting a different independent task.",
                },
            }
        }
        res = self._predict_with_laya(prompt, questions)
        if res and "answers" in res and "matches_waiting_subagent" in res["answers"]:
            ans = res["answers"]["matches_waiting_subagent"]
            choice = ans.get("choice")
            probs = ans.get("probabilities", {})
            prob = probs.get("matches", 0.0)
            return (choice == "matches"), prob

        # Deterministic fallback
        prompt_lower = prompt.lower()
        waiting_lower = waiting_agent.lower()
        if f"@{waiting_lower}" in prompt_lower or any(
            token in prompt_lower for token in ["approve", "reject", "proceed", "looks good", "lgtm", "change", "modify", "spec", "plan"]
        ):
            return True, 0.90
        return False, 0.50

    def evaluate_intent(self, prompt: str) -> tuple[str, float]:
        """Stage 3: Triage prompt into question, coding, or monitoring."""
        questions = {
            "intent": {
                "type": "choice",
                "instructions": "Classify the primary intent into: question, coding, or monitoring.",
                "criteria": {
                    "question": "Asking for explanations, code review, inquiries, or information without requesting new code implementation or modifications.",
                    "coding": "Asking to create, modify, implement, refactor, test, or build code, or running a development workflow.",
                    "monitoring": "Asking to monitor, watch, stream, inspect logs, or track serial console/application runtime errors.",
                },
            }
        }
        res = self._predict_with_laya(prompt, questions)
        if res and "answers" in res and "intent" in res["answers"]:
            ans = res["answers"]["intent"]
            choice = ans.get("choice", "question")
            probs = ans.get("probabilities", {})
            prob = probs.get(choice, ans.get("answer_confidence", 0.85))
            return choice, prob

        # Deterministic fallback
        prompt_lower = prompt.lower()
        if any(w in prompt_lower for w in ["monitor", "watch logs", "tail -f", "serial console", "log stream", "@monitoring"]):
            return "monitoring", 0.92
        if any(w in prompt_lower for w in ["write", "create", "implement", "build", "refactor", "bugfix", "fix", "feature", "@coding"]):
            return "coding", 0.90
        return "question", 0.85

    def triage(
        self,
        prompt: str,
        invocation_num: int = 1,
        state: Optional[WorkflowState] = None,
    ) -> TriageResult:
        """Run the 3-stage triage pipeline."""
        if state is None:
            state = WorkflowState()

        inject_steps: list[dict[str, Any]] = []

        # -------------------------------------------------------------
        # Stage 1: Session Scope Check
        # -------------------------------------------------------------
        in_scope, scope_conf = self.evaluate_scope(prompt, invocation_num)
        if not in_scope or scope_conf < 0.80:
            inject_steps.append({
                "systemMessage": {
                    "systemMessage": (
                        "Prompt Triage Alert: The prompt appears out of the scope of this session "
                        f"(confidence: {scope_conf:.2f}). Ask the user whether they want to "
                        "broaden the scope of the session or stop here."
                    )
                }
            })
            return TriageResult(
                stage_reached=1,
                in_scope=in_scope,
                scope_confidence=scope_conf,
                inject_steps=inject_steps,
            )

        # -------------------------------------------------------------
        # Stage 2: Check Active Workflow & Waiting Subagent
        # -------------------------------------------------------------
        if state.status.is_waiting_user_input() and state.waiting_agent:
            matches, match_conf = self.evaluate_waiting_agent_match(prompt, state.waiting_agent)
            if matches and match_conf >= 0.80:
                conv_target = state.waiting_conversation_id or state.waiting_agent
                inject_steps.append({
                    "systemMessage": {
                        "systemMessage": (
                            f"Prompt Triage: Routed to waiting subagent '{state.waiting_agent}' "
                            f"(Target: {conv_target}). Deliver the prompt directly to '{state.waiting_agent}' "
                            f"using send_message to resume workflow step '{state.current_step}'."
                        )
                    }
                })
                return TriageResult(
                    stage_reached=2,
                    in_scope=True,
                    scope_confidence=scope_conf,
                    routed_to_waiting_agent=state.waiting_agent,
                    inject_steps=inject_steps,
                )

        # -------------------------------------------------------------
        # Stage 3: Intent Classification (Question, Coding, Monitoring)
        # -------------------------------------------------------------
        intent, intent_conf = self.evaluate_intent(prompt)

        if intent_conf < 0.80:
            # Low confidence: instruct agent to ask user to confirm
            inject_steps.append({
                "systemMessage": {
                    "systemMessage": (
                        f"Prompt Triage: Intent classification is uncertain (tentative: {intent}, confidence: {intent_conf:.2f}). "
                        "Please ask the user to confirm if their request is a Question, Coding Request, or Monitoring Request."
                    )
                }
            })
            return TriageResult(
                stage_reached=3,
                in_scope=True,
                scope_confidence=scope_conf,
                intent=intent,
                intent_confidence=intent_conf,
                inject_steps=inject_steps,
            )

        if intent == "question":
            inject_steps.append({
                "ephemeralMessage": "Prompt Triage Directive: Do not make any changes."
            })
        elif intent == "coding":
            if state.status.is_active():
                inject_steps.append({
                    "systemMessage": {
                        "systemMessage": (
                            f"Prompt Triage: A coding workflow is already active (ID: {state.workflow_id}, Step: {state.current_step}). "
                            f"Current waiting agent: {state.waiting_agent or 'None'}."
                        )
                    }
                })
            else:
                inject_steps.append({
                    "systemMessage": {
                        "systemMessage": (
                            "Prompt Triage: Coding request identified. Please invoke the coding-orchestrator subagent (@coding) "
                            "using invoke_subagent to initiate the workflow (coding-clarify -> coding-specify -> coding-plan -> coding-develop -> coding-review -> coding-merge)."
                        )
                    }
                })
        elif intent == "monitoring":
            inject_steps.append({
                "systemMessage": {
                    "systemMessage": (
                        "Prompt Triage: Monitoring request identified. Please invoke the coding-monitoring subagent (@monitoring) "
                        "using invoke_subagent to track the requested log stream or console output."
                    )
                }
            })

        return TriageResult(
            stage_reached=3,
            in_scope=True,
            scope_confidence=scope_conf,
            intent=intent,
            intent_confidence=intent_conf,
            inject_steps=inject_steps,
        )
