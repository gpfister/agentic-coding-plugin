---
name: coding-orchestrator
description: >-
  Orchestrate full-lifecycle software development tasks through the 6-stage
  coordinated workflow: coding-clarify, coding-specify, coding-plan,
  coding-develop, coding-review, and coding-merge.
---

# Coding Orchestrator (`@coding`)

The `coding-orchestrator` guides software requests through a rigorous, multi-agent development pipeline.

## Workflow Pipeline

1. **`coding-clarify`**:
   - Conducts a Matt Pocock `/grill-me` style interview.
   - Clarifies edge cases, non-goals, and dependencies one question at a time via `ask_question`.
2. **`coding-specify`**:
   - Synthesizes findings into `specification.md` (Artifact).
   - Awaits user approval, rejection, or feedback in the background.
3. **`coding-plan`**:
   - Decomposes work per repository and determines branch names (`feature/*`, `task/*`, `bugfix/*`).
   - Produces `plan.md` (Artifact) and awaits user approval.
4. **`coding-develop`**:
   - Fanned out in parallel per repository (`coding-develop-<repo>`).
   - Scoped strictly to each repo directory. Writes code, tests, documentation, and verifies linting.
5. **`coding-review`**:
   - Collects all develop reports. Confirms cross-repo consistency and spec compliance.
   - If defects found, loops back to `coding-plan`. If approved, asks user for merge confirmation.
6. **`coding-merge`**:
   - Automatically merges locally or opens a Pull Request with `gh` if remote exists.

## Triggering the Workflow

- Type `@coding <your feature or task description>`
- Or prompt: "Implement the following feature using the coding workflow: ..."
