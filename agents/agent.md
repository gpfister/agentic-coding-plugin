---
name: agent
description: Subagent architecture, registry catalog, and 6-stage software development lifecycle workflow guide.
---

# Agentic Coding Subagents & Workflow (`agents/agent.md`)

This document defines the subagent architecture, the registry of specialized worker agents, and the end-to-end coding workflow for the **`agentic-coding-plugin`**.

---

## 1. Architectural Overview

The `agentic-coding-plugin` organizes agent capabilities into modular, declarative, markdown-defined subagents. Rather than burdening a single agent with every phase of the software engineering lifecycle, the plugin partitions tasks across specialized subagents invoked via `invoke_subagent`.

### 1.1 Directory Structure
Each subagent resides in its own isolated directory under `agents/<agent>/` containing its markdown definition:

```text
agents/
├── agent.md                        # Master subagent & workflow specification (this file)
├── coding/                         # Coding Workflow Orchestrator
│   ├── agent.md -> coding.md
│   └── coding.md
├── coding-clarify/                 # Stage 1: Requirement Clarifier
│   ├── agent.md -> coding-clarify.md
│   └── coding-clarify.md
├── coding-specify/                 # Stage 2: Specification Architect
│   ├── agent.md -> coding-specify.md
│   └── coding-specify.md
├── coding-plan/                    # Stage 3: Architecture Planner
│   ├── agent.md -> coding-plan.md
│   └── coding-plan.md
├── coding-develop/                 # Stage 4: Per-Repo Software Engineer
│   ├── agent.md -> coding-develop.md
│   └── coding-develop.md
├── coding-review/                  # Stage 5: QA Gatekeeper
│   ├── agent.md -> coding-review.md
│   └── coding-review.md
├── coding-merge/                   # Stage 6: Release & Merge Engineer
│   ├── agent.md -> coding-merge.md
│   └── coding-merge.md
├── coding-investigate/             # Standalone Issue Investigator
│   ├── agent.md -> coding-investigate.md
│   └── coding-investigate.md
├── coding-monitoring/              # Telemetry & Stream Monitor
│   ├── agent.md -> coding-monitoring.md
│   └── coding-monitoring.md
└── monitoring/                     # Short alias for coding-monitoring
    ├── agent.md -> monitoring.md
    └── monitoring.md
```

### 1.2 Subagent Registration & Tool Privilege Model
Subagents are discovered dynamically and registered during `SessionStart` via [`hooks/register_subagents.py`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/hooks/register_subagents.py) using `define_subagent` (or `define_agent`):

| Agent Handle | Directory | `enable_write_tools` | `enable_subagent_tools` | `enable_mcp_tools` | Primary Responsibility |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **`@coding`** | [`agents/coding/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/coding/) | `True` | `True` | `True` | 6-stage lifecycle pipeline orchestration |
| **`@coding-clarify`** | [`agents/coding-clarify/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/coding-clarify/) | `True` | `False` | `True` | One-question-at-a-time requirement interrogation |
| **`@coding-specify`** | [`agents/coding-specify/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/coding-specify/) | `True` | `False` | `True` | Specification authoring & interactive approval gate |
| **`@coding-plan`** | [`agents/coding-plan/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/coding-plan/) | `True` | `False` | `True` | Multi-repo task breakdown & branch planning |
| **`@coding-develop`** | [`agents/coding-develop/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/coding-develop/) | `True` | `False` | `True` | Isolated repo implementation, tests, linting, docs |
| **`@coding-review`** | [`agents/coding-review/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/coding-review/) | `True` | `False` | `True` | Deliverables verification against specification |
| **`@coding-merge`** | [`agents/coding-merge/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/coding-merge/) | `True` | `False` | `True` | Local branch merge or GitHub Pull Request (`gh pr create`) |
| **`@coding-investigate`**| [`agents/coding-investigate/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/coding-investigate/) | `True` | `True` | `True` | Multi-repo defect investigation & remediation handoff |
| **`@coding-monitoring`** | [`agents/coding-monitoring/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/coding-monitoring/) | `True` | `False` | `True` | Streaming surveillance of logs, Docker, and serial ports |
| **`@monitoring`** | [`agents/monitoring/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/monitoring/) | `True` | `False` | `True` | Alias for `@coding-monitoring` |

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
- **Handoff**: Concludes with structured `ClarificationSummary` JSON transferred to `coding-specify`.

### Stage 2: Specification (`coding-specify`)
- **Objective**: Author a comprehensive, verifiable technical specification document (`specification.md`).
- **Contents**: Problem motivation, functional requirements, non-functional requirements, affected repositories, test contracts, and edge-case mitigations.
- **Interactive Approval Gate**: Requires user approval via Antigravity's interactive modal before proceeding.

### Stage 3: Planning (`coding-plan`)
- **Objective**: Deconstruct the approved specification into atomic, verifiable steps and determine git branch names (`plan.md`).
- **Multi-Repository Isolation**:
  - Assigns work strictly per repository (respecting workspace boundaries).
  - Branch conventions: `feature/<name>` (new capabilities), `task/<name>` (maintenance/refactoring), `bugfix/<name>` (bug fixes).
- **Interactive Approval Gate**: Requires user approval via Antigravity's interactive modal before starting development.

### Stage 4: Development (`coding-develop`)
- **Objective**: Implement required code changes, tests, linters, documentation, and CI/CD updates.
- **Parallel Fan-Out**: When multiple repositories are affected, `@coding` spawns independent `coding-develop` workers per repo in parallel (`coding-develop-<repo>`).
- **Quality Mandates**:
  - Run all unit and integration tests; verify 100% clean passes.
  - Preserve all existing comments and docstrings unrelated to code changes.
  - Output structured `DevelopReport` JSON summarizing modified files and test outputs.

### Stage 5: Review (`coding-review`)
- **Objective**: Validate all deliverables against the original specification and verify cross-repo contract compatibility.
- **Discrepancy Routing**:
  - If regressions or specification discrepancies are found: Route issues back to `coding-plan` with actionable feedback.
  - If approved: Present validation summary to the user and request confirmation to proceed to merge.

### Stage 6: Merge & Release (`coding-merge`)
- **Objective**: Safely integrate approved changes into repository release branches.
- **Merge Strategy**:
  - **No Remote Repository**: Checkout base branch (`master`/`main`) and execute local `git merge <branch>`.
  - **Remote Repository Configured**: Push branch to origin (`git push origin <branch>`) and create a Pull Request via GitHub CLI (`gh pr create`).

---

## 3. Specialized Workflows

### 3.1 Standalone Issue Investigation (`@coding-investigate`)
For bugs, anomalies, and test failures, `@coding-investigate` runs an autonomous multi-repository investigation:
1. Search code, error messages, stack traces, configs, and git history across all repositories.
2. Formulate root cause analysis and proposed remediation in an `issue-assessment.md` artifact.
3. Submit `issue-assessment.md` for interactive user approval (`RequestFeedback=True`).
4. Upon user approval, confirm whether to begin automated correction; if confirmed, invoke `@coding` to execute the 6-stage lifecycle.

### 3.2 Telemetry & Stream Surveillance (`@monitoring` / `@coding-monitoring`)
For long-running tasks, Docker logs, serial consoles (`/dev/tty*`), or continuous build streams:
1. Stream output continuously while scanning for error patterns and stack traces.
2. Upon anomaly detection, immediately pause surveillance and formulate a `MonitoringAlert` JSON.
3. Prompt the user with intervention options (Restart, Ignore, Abort, Inspect code) via `ask_question`.

---

## 4. Antigravity Interactive Artifact Approval Protocol

Artifacts requiring human confirmation (`specification.md`, `plan.md`, `issue-assessment.md`) must trigger the interactive **Approve / Reject** modal in the Antigravity UI:

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
   - Stop calling tools immediately after writing the artifact to yield the turn to the user.
4. **Handling Feedback**:
   - `[Approved] <artifact>.md`: Advance immediately to the next stage.
   - `[Rejected] <artifact>.md`: Re-route user comments back to the authoring subagent to adjust scope and re-synthesize.
