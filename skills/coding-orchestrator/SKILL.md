---
name: coding
description: >-
  Orchestrate full-lifecycle software development tasks through the 6-stage
  coordinated workflow: coding-clarify, coding-specify, coding-plan,
  coding-develop, coding-review, and coding-merge.
---

# Coding Orchestrator (`@coding`)

The `coding` subagent guides software requests through a rigorous, multi-agent development pipeline.

## Workflow Pipeline

1. **`coding-clarify`**:
   - Conducts a Matt Pocock `/grill-me` style interview.
   - Clarifies edge cases, non-goals, and dependencies one question at a time via `ask_question`.
2. **`coding-specify`**:
   - Synthesizes findings into `specification.md` (Artifact with `RequestFeedback=True`).
   - Awaits interactive user approval in the background (`idle` state).
   - **Idle Guard**: Orchestrator ignores `has gone idle` platform notifications, halts turn execution without calling tools, and awaits explicit subagent approval message.
   - Advances to `coding-plan` ONLY upon receiving explicit `[GATE_APPROVED] specification.md:` message from `coding-specify` (or routes to `coding-clarify` on `[GATE_REJECTED]`).
3. **`coding-plan`**:
   - Decomposes work per repository and determines branch names (`feature/*`, `task/*`, `bugfix/*`).
   - Produces `plan.md` (Artifact with `RequestFeedback=True`) and awaits user approval in the background (`idle` state).
   - **Idle Guard**: Orchestrator ignores `has gone idle` platform notifications, halts turn execution without calling tools, and awaits explicit subagent approval message.
   - Advances to `coding-develop` ONLY upon receiving explicit `[GATE_APPROVED] plan.md:` message from `coding-plan` (or routes to `coding-clarify` on `[GATE_REJECTED]`).
4. **`coding-develop`**:
   - Fanned out in parallel per repository (`coding-develop-<repo>`).
   - Scoped strictly to each repo directory. Writes code, tests, documentation, and verifies linting.
5. **`coding-review`**:
   - Collects all develop reports. Confirms cross-repo consistency and spec compliance.
   - If defects found, loops back to `coding-plan`. If approved, asks user for merge confirmation.
6. **`coding-merge`**:
   - Automatically merges locally or opens a Pull Request with `gh` if remote exists.

## Interactive Approval Gate & Idle Guard Protocol

- `coding-specify` and `coding-plan` write artifacts (`specification.md`, `plan.md`) with `RequestFeedback=True` as their sole and final tool call, entering `idle` state.
- When Antigravity notifies `Subagent <id> has gone idle`, the orchestrator **MUST NOT** proceed to the next stage. It terminates its turn immediately without calling tools.
- Advancement to Stage 3 or Stage 4 requires an explicit message starting with `[GATE_APPROVED]` (e.g. `[GATE_APPROVED] specification.md:` or `[GATE_APPROVED] plan.md:`).
- Rejection or change requests starting with `[GATE_REJECTED]` route back to `coding-clarify`.

## Triggering the Workflow

- Type `@coding <your feature or task description>`
- Or prompt: "Implement the following feature using the coding workflow: ..."
