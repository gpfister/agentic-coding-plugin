---
name: coding-catalog
description: Subagent architecture, registry catalog, and 6-stage software development lifecycle workflow guide.
enable_write_tools: false
enable_subagent_tools: false
enable_mcp_tools: false
tools:
  - read_file
  - list_dir
---

# Agentic Coding Subagents & Workflow (`agents/agent.md`)

This document defines the subagent architecture, the registry of specialized worker agents, and the end-to-end coding workflow for the **`agentic-coding-plugin`**.

---

## 1. Architectural Overview

The `agentic-coding-plugin` organizes agent capabilities into modular, declarative, markdown-defined subagents. Rather than burdening a single agent with every phase of the software engineering lifecycle, the plugin partitions tasks across specialized subagents coordinated by the `@coding` orchestrator.

### 1.1 Directory Structure
Each subagent resides in its own isolated directory under `agents/<agent>/` containing its markdown definition:

```text
agents/
├── agent.md                        # Master subagent & workflow specification (this file)
├── coding/                         # Coding Workflow Orchestrator
│   └── agent.md
├── coding-clarify/                 # Stage 1: Requirement Clarifier
│   └── agent.md
├── coding-specify/                 # Stage 2: Specification Architect
│   └── agent.md
├── coding-plan/                    # Stage 3: Architecture Planner
│   └── agent.md
├── coding-develop/                 # Stage 4: Per-Repo Software Engineer
│   └── agent.md
├── coding-review/                  # Stage 5: QA Gatekeeper
│   └── agent.md
└── coding-merge/                   # Stage 6: Release & Merge Engineer
    └── agent.md
```

### 1.2 Subagent Registration & Tool Privilege Model
Subagents are discovered dynamically and registered via `define_subagent` (or `define_agent`):

| Agent Handle | Directory | `enable_write_tools` | `enable_subagent_tools` | `enable_mcp_tools` | Allowed Tools | Primary Responsibility |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| **`@coding`** | [`agents/coding/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/coding/) | `True` | `True` | `True` | `invoke_subagent`, `send_message`, `manage_subagents`, `ask_question`, `read_file`, `list_dir`, `run_command` | 6-stage lifecycle pipeline orchestration |
| **`@coding-clarify`** | [`agents/coding-clarify/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/coding-clarify/) | `False` | `False` | `True` | `ask_question`, `read_file`, `list_dir`, `search_web` | One-question-at-a-time requirement interrogation |
| **`@coding-specify`** | [`agents/coding-specify/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/coding-specify/) | `True` | `False` | `True` | `write_file`, `read_file`, `list_dir`, `search_web`, `send_message` | Specification authoring & interactive approval gate |
| **`@coding-plan`** | [`agents/coding-plan/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/coding-plan/) | `True` | `False` | `True` | `write_file`, `read_file`, `list_dir`, `run_command`, `send_message` | Multi-repo task breakdown & branch planning |
| **`@coding-develop`** | [`agents/coding-develop/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/coding-develop/) | `True` | `False` | `True` | `read_file`, `write_file`, `edit_file`, `list_dir`, `run_command`, `search_web` | Isolated repo implementation, tests, linting, docs |
| **`@coding-review`** | [`agents/coding-review/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/coding-review/) | `True` | `False` | `True` | `read_file`, `list_dir`, `run_command`, `ask_question` | Deliverables verification against specification |
| **`@coding-merge`** | [`agents/coding-merge/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/coding-merge/) | `True` | `False` | `True` | `run_command`, `read_file`, `list_dir`, `ask_question` | Local branch merge or GitHub Pull Request (`gh pr create`) |

---

## 2. The 6-Stage Coding Workflow

The core software development lifecycle executes sequentially across 6 distinct phases coordinated by the `@coding` orchestrator:

```text
coding-clarify ──> coding-specify ──> coding-plan ──> coding-develop (parallel per repo)
                          ▲               ▲                      │
                          │ (reject/fb)   │ (reject/fb)          ▼
                          └───────────────┴────────────── coding-review
                                                                 │ (approved)
                                                                 ▼
                                                           coding-merge
```

### Stage 1: Clarification (`coding-clarify`)
- **Objective**: Interrogate ambiguities, hidden assumptions, edge cases, and scope boundaries before designing solutions.
- **Grill-Me Protocol**:
  - Never ask open-ended or bundled batches of questions. Always ask **one question at a time** via `ask_question`.
  - For each question provide: why the decision matters, concrete options, a recommended option prefixed with `(Recommended)`, and the technical rationale.
  - **Inspect First Rule**: Check existing codebase files before asking questions that can be answered from inspection.
- **Handoff**: Concludes with structured `ClarificationSummary` JSON transferred back to `@coding` to transition to `coding-specify`.

### Stage 2: Specification (`coding-specify`)
- **Objective**: Author a comprehensive, verifiable technical specification document (`specification.md`).
- **Contents**: Problem motivation, functional requirements, non-functional requirements, affected repositories, test contracts, and edge-case mitigations.
- **Interactive Approval Gate & Idle Guard**:
  - `coding-specify` writes `specification.md` with `RequestFeedback=True` as its sole and final tool call, then enters the `idle` state.
  - When Antigravity notifies `Subagent <id> has gone idle`, `@coding` must **halt and remain idle** without invoking subagents.
  - `@coding` advances to Stage 3 (`coding-plan`) **only** upon receiving an explicit `[GATE_APPROVED] specification.md:` message from `coding-specify`.

### Stage 3: Planning (`coding-plan`)
- **Objective**: Deconstruct the approved specification into atomic, verifiable steps and determine git branch names (`plan.md`).
- **Multi-Repository Isolation**:
  - Assigns work strictly per repository (respecting workspace boundaries).
  - Branch conventions: `feature/<name>` (new capabilities), `task/<name>` (maintenance/refactoring), `bugfix/<name>` (bug fixes).
- **Interactive Approval Gate & Idle Guard**:
  - `coding-plan` writes `plan.md` with `RequestFeedback=True` as its sole and final tool call, then enters the `idle` state.
  - When Antigravity notifies `Subagent <id> has gone idle`, `@coding` must **halt and remain idle** without invoking subagents.
  - `@coding` advances to Stage 4 (`coding-develop`) **only** upon receiving an explicit `[GATE_APPROVED] plan.md:` message from `coding-plan`.

### Stage 4: Development (`coding-develop`)
- **Objective**: Implement required code changes, tests, linters, documentation, and CI/CD updates.
- **Parallel Fan-Out**: When multiple repositories are affected, `@coding` spawns independent `coding-develop` workers per repo in parallel (`coding-develop-<repo>`).
- **Quality Mandates**:
  - Run all unit and integration tests; verify 100% clean passes.
  - Preserve all existing comments and docstrings unrelated to code changes.
  - Output structured `DevelopReport` JSON summarizing modified files and test outputs back to `@coding`.

### Stage 5: Review (`coding-review`)
- **Objective**: Validate all deliverables against the original specification and verify cross-repo contract compatibility.
- **Discrepancy Routing**:
  - If regressions or specification discrepancies are found: Route issues back to `coding-plan` via `@coding` with actionable feedback.
  - If approved: Present validation summary to the user and request confirmation to proceed to merge.

### Stage 6: Merge & Release (`coding-merge`)
- **Objective**: Safely integrate approved changes into repository release branches.
- **Merge Strategy**:
  - **No Remote Repository**: Checkout base branch (`master`/`main`) and execute local `git merge <branch>`.
  - **Remote Repository Configured**: Push branch to origin (`git push origin <branch>`) and create a Pull Request via GitHub CLI (`gh pr create`).

---

## 3. Companion Plugins & Workflows

### 3.1 Autonomous Issue Investigation (`@investigate`)
For complex bugs, defects, test failures, or cross-repository diagnostic tasks, use the companion plugin **`agentic-investigate-plugin`** (`@investigate`), which performs autonomous root cause analysis, user interrogation, and hands off approved fixes to `@coding`.

### 3.2 External Telemetry & Stream Surveillance (`@monitoring`)
For long-running tasks, Docker logs, serial consoles (`/dev/tty*`), or continuous build streams, use the companion plugin **`agentic-monitoring-plugin`** (`@monitoring`), which provides real-time streaming surveillance with interactive anomaly pause gates.

---

## 4. Antigravity Interactive Artifact Approval Protocol

Artifacts requiring human confirmation (`specification.md`, `plan.md`) must trigger the interactive **Approve / Reject** modal in the Antigravity UI:

1. **Artifact Location**: Write directly to the conversation artifact directory:
   `<appDataDir>/brain/<conversation-id>/<artifact_name>.md`.
2. **Artifact Metadata**: Always supply `ArtifactMetadata` with `RequestFeedback=True` and `UserFacing=True`:
   ```python
   write_file(
       Path=f"{artifact_dir}/specification.md",
       Content=spec_content,
       Overwrite=True,
       ArtifactMetadata={
           "RequestFeedback": True,
           "UserFacing": True,
           "Summary": "Technical specification for user review and approval."
       }
   )
   ```
3. **Sole & Final Tool Call Rule (CRITICAL)**:
   - To trigger the interactive modal, `write_file(..., RequestFeedback=True)` MUST be the **sole and final tool call of that turn**.
   - Never batch secondary tool calls (e.g. running shell commands, writing Obsidian notes, sending messages) in the same turn.
   - Stop calling tools immediately after writing the artifact to yield the turn to the user and enter the `idle` state.
4. **Subagent Idle vs Approval Disambiguation Guard**:
   - When a gatekeeper subagent (`coding-specify` or `coding-plan`) writes an artifact and enters `idle`, Antigravity notifies the orchestrator: `Subagent <id> has gone idle`.
   - **DO NOT proceed to the next stage upon receiving `Subagent <id> has gone idle`!** The orchestrator must terminate its turn without calling any tools and remain idle.
5. **Handling User Decisions & Gate Messages**:
   - On interactive approval (`[Approved] <artifact>.md`), the subagent sends:
     `send_message(Recipient="<orchestrator_id>", Message="[GATE_APPROVED] <artifact>.md: ...")`
     The orchestrator then advances to the subsequent stage (`coding-plan` after `specification.md`, `coding-develop` after `plan.md`).
   - On interactive rejection or comments (`[Rejected] <artifact>.md`), the subagent sends:
     `send_message(Recipient="<orchestrator_id>", Message="[GATE_REJECTED] <artifact>.md: <User Feedback>")`
     The orchestrator routes feedback back to `coding-clarify` to resume the clarification loop.
