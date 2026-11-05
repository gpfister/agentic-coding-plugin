---
name: coding-catalog
description: Subagent architecture, registry catalog, and 7-stage software development lifecycle workflow guide.
enable_write_tools: false
enable_subagent_tools: false
enable_mcp_tools: false
tools:
  - read_file
  - list_dir
---

# Coding - Agentic Coding Subagents & Workflow (agents/agent.md)

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
├── coding-deploy/                  # Stage 5: Local Deployment Specialist
│   └── agent.md
├── coding-review/                  # Stage 6: QA Gatekeeper
│   └── agent.md
└── coding-merge/                   # Stage 7: Release & Merge Engineer
    └── agent.md
```

### 1.2 Subagent Registration & Tool Privilege Model
Subagents are discovered dynamically and registered via `define_subagent` (or `define_agent`):

| Agent Handle | Directory | `enable_write_tools` | `enable_subagent_tools` | `enable_mcp_tools` | Allowed Tools | Primary Responsibility |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| **`@coding`** | [`agents/coding/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/coding/) | `True` | `True` | `True` | `invoke_subagent`, `send_message`, `manage_subagents`, `ask_question`, `read_file`, `list_dir`, `run_command` | 7-stage lifecycle pipeline orchestration |
| **`@coding-clarify`** | [`agents/coding-clarify/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/coding-clarify/) | `False` | `False` | `True` | `ask_question`, `read_file`, `list_dir`, `search_web`, `send_message` | One-question-at-a-time requirement interrogation with Question Relay Protocol |
| **`@coding-specify`** | [`agents/coding-specify/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/coding-specify/) | `True` | `False` | `True` | `write_file`, `read_file`, `list_dir`, `search_web`, `send_message` | Specification authoring & interactive approval gate |
| **`@coding-plan`** | [`agents/coding-plan/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/coding-plan/) | `True` | `False` | `True` | `write_file`, `read_file`, `list_dir`, `run_command`, `send_message` | Multi-repo task breakdown, deployment assessment, & branch planning |
| **`@coding-develop`** | [`agents/coding-develop/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/coding-develop/) | `True` | `False` | `True` | `read_file`, `write_file`, `edit_file`, `list_dir`, `run_command`, `search_web` | Isolated repo implementation, tests, linting, docs, and fix remediation |
| **`@coding-deploy`** | [`agents/coding-deploy/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/coding-deploy/) | `True` | `True` | `True` | `run_command`, `read_file`, `list_dir`, `write_file`, `edit_file`, `ask_question`, `send_message`, `invoke_subagent` | Local deployment execution, health monitoring, error investigation & fix orchestration |
| **`@coding-review`** | [`agents/coding-review/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/coding-review/) | `True` | `False` | `True` | `read_file`, `list_dir`, `run_command`, `ask_question`, `send_message` | Deliverables and deployment verification against specification; merge confirmation relay |
| **`@coding-merge`** | [`agents/coding-merge/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/coding-merge/) | `True` | `False` | `True` | `run_command`, `read_file`, `list_dir`, `ask_question` | Local branch merge or GitHub Pull Request (`gh pr create`) |

---

## 2. The 7-Stage Coding Workflow

The core software development lifecycle executes sequentially across 7 distinct phases coordinated by the `@coding` orchestrator:

```text
coding-clarify ──> coding-specify ──> coding-plan ──> coding-develop (parallel per repo)
                          ▲               ▲                      │
                          │               │                      ▼
                          │ (reject/fb)   │ (reject/fb)   coding-deploy (immediate per repo)
                          │               │                      │
                          └───────────────┴────────────── coding-review (all dev + deploy done)
                                                                 │ (approved)
                                                                 ▼
                                                           coding-merge
```

### Stage 1: Clarification (`coding-clarify`)
- **Objective**: Interrogate ambiguities, hidden assumptions, edge cases, and scope boundaries before designing solutions.
- **Grill-Me Protocol**:
  - Never ask open-ended or bundled batches of questions. Always ask **one question at a time**.
  - **Question Relay Protocol**: When running under `@coding` (caller ID present), send questions to `@coding` using `[QUESTION_RELAY_REQUEST]`. `@coding` prompts the user via `ask_question` and replies with `[QUESTION_RELAY_RESPONSE]`. Standalone invocations fall back to direct `ask_question`.
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
- **Objective**: Deconstruct the approved specification into atomic, verifiable steps, assess local deployment requirements, and determine git branch names (`plan.md`).
- **Local Deployment Assessment**:
  - `coding-plan` inspects each target repository for local deployment mechanisms (Docker, docker-compose, scripts/deployment_local.sh, terraform/local, Minikube/Kubernetes manifests).
  - Explicitly adds local deployment tasks for repositories requiring them.
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
- **Immediate Per-Repo Deployment Trigger**:
  - As each repository's development concludes, if that repository contains local deployment instructions, Stage 5 (`coding-deploy`) is triggered immediately for that repository.

### Stage 5: Local Deployment (`coding-deploy`)
- **Objective**: Execute local deployment and monitor health in real time to ensure containerized services, local clusters (e.g. Minikube), or local runtimes deploy properly.
- **Trigger**: Invoked one time for every repository containing local deployment instructions, immediately following the completion of that repository's `coding-develop` step.
- **Monitoring**: Actively monitors container statuses, pod states (`kubectl get pods`), and service endpoints (`curl -fsS http://localhost:<port>/health`).
- **Error Investigation & Self-Healing Protocol**:
  - If a deployment failure or unhealthy probe occurs:
    1. Investigate the failure and extract diagnostic evidence (logs, pod descriptions, events).
    2. Author a `Deployment Issue` artifact (`deployment-issue.md`) with `RequestFeedback=True` as the sole and final tool call of the turn.
    3. Await user decision at the approval gate.
    4. If approved: if multiple solutions were proposed, prompt the user to choose the desired fix (relaying via `[QUESTION_RELAY_REQUEST]` under `@coding`, or calling `ask_question` directly in standalone mode).
    5. Invoke `coding-develop` to implement the approved fix.
    6. Re-deploy and verify health until clean or user aborts.
- **Handoff**: Concludes with structured `DeployReport` JSON.

### Stage 6: Review (`coding-review`)
- **Objective**: Validate all deliverables against the original specification, verify cross-repo contract compatibility, and confirm that all required local deployments succeeded.
- **Discrepancy Routing**:
  - If regressions or specification discrepancies are found: Route issues back to `coding-plan` via `@coding` with actionable feedback.
  - If approved: Present validation summary to the user and request confirmation to proceed to merge (relaying via `[QUESTION_RELAY_REQUEST]` under `@coding`, or handled directly by `@coding` via `ask_question` in Phase 6).

### Stage 7: Release & Merge (`coding-merge`)
- **Objective**: Safely integrate approved changes into repository release branches.
- **Prerequisite**: `@coding-merge` strictly waits for all `coding-deploy` and all `coding-develop` tasks to have completed successfully before proceeding.
- **Merge Strategy**:
  - **No Remote Repository**: Checkout base branch (`master`/`main`) and execute local `git merge <branch>`.
  - **Remote Repository Configured**: Push branch to origin (`git push origin <branch>`) and create a Pull Request via GitHub CLI (`gh pr create`).

---

## 3. Companion Plugins & Workflows

### 3.1 Autonomous Issue Investigation (`@coding-investigate`)
For complex bugs, defects, test failures, or cross-repository diagnostic tasks, use the companion plugin **`agentic-issue-investigation-plugin`** (`@coding-investigate`), which performs autonomous root cause analysis, user interrogation, and hands off approved fixes to `@coding`.

### 3.2 External Telemetry & Stream Surveillance (`@coding-monitor`)
For long-running tasks, Docker logs, serial consoles (`/dev/tty*`), or continuous build streams, use the companion plugin **`agentic-task-monitoring-plugin`** (`@coding-monitor`), which provides real-time streaming surveillance with interactive anomaly pause gates.

### 3.3 Documentation Archival & Obsidian Vault Integration (`@coding-document`)
For persistent documentation across projects, features, architecture designs, ADRs, session logs, and git status updates, use the companion plugin **`agentic-project-documenting-plugin`** (`@coding-document`), invoked by `@coding` only after the plan is approved, before merging, and at the end of the lifecycle.

### 3.4 Deep Web & Literature Research (`@coding-research`)
For autonomous topic investigations, technology evaluations, documentation searches, and comparative research reports, use the companion plugin **`agentic-topic-researching-plugin`** (`@coding-research`).

### 3.5 Interactive Project Grooming (`/project-grooming`)
For interactive requirements interrogation, backlog grooming, scope boundary clarification, and repository bootstrapping, use the companion plugin **`agentic-project-grooming-plugin`**.

### 3.6 Dynamic Prompt Triage
For fast non-autoregressive prompt classification and intent routing across installed plugins, use the companion plugin **`agentic-prompt-triage-plugin`**.

---

## 4. Antigravity Interactive Artifact Approval Protocol

Artifacts requiring human confirmation (`specification.md`, `plan.md`, `deployment-issue.md`) must trigger the interactive **Approve / Reject** modal in the Antigravity UI:

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
   - When a gatekeeper subagent (`coding-specify`, `coding-plan`, or `coding-deploy`) writes an artifact and enters `idle`, Antigravity notifies the orchestrator: `Subagent <id> has gone idle`.
   - **DO NOT proceed to the next stage upon receiving `Subagent <id> has gone idle`!** The orchestrator must terminate its turn without calling any tools and remain idle.
5. **Handling User Decisions & Gate Messages**:
   - On interactive approval (`[Approved] <artifact>.md`), the subagent sends:
     `send_message(Recipient="<orchestrator_id>", Message="[GATE_APPROVED] <artifact>.md: ...")`
     The orchestrator then advances to the subsequent stage (`coding-plan` after `specification.md`, `coding-develop` after `plan.md`).
   - On interactive rejection or comments (`[Rejected] <artifact>.md`), the subagent sends:
     `send_message(Recipient="<orchestrator_id>", Message="[GATE_REJECTED] <artifact>.md: <User Feedback>")`
     The orchestrator routes feedback back to `coding-clarify` to resume the clarification loop.

---

## 5. Question Relay Protocol (`[QUESTION_RELAY_REQUEST]` / `[QUESTION_RELAY_RESPONSE]`)

Worker subagents do not execute interactive user prompts directly when managed by `@coding`. Instead, they delegate interactive user queries to the parent orchestrator using structured message contracts:

### 5.1 Protocol Message Contracts
- **Relay Request (`Subagent -> @coding`)**:
  ```text
  [QUESTION_RELAY_REQUEST]
  Question: <Question text>
  Options:
  - (Recommended) Option 1: <Description>
  - Option 2: <Description>
  Context: <Rationale and background>
  ```
- **Relay Response (`@coding -> Subagent`)**:
  ```text
  [QUESTION_RELAY_RESPONSE]
  Answer: <selected_option_or_text>
  ```

### 5.2 Orchestrator Handling & Timeout Mitigation Patterns
1. **Interactive Prompt Handling**: Upon receiving `[QUESTION_RELAY_REQUEST]`, the orchestrator parses the question, options, and context, calls `ask_question` at the top level, and immediately sends `[QUESTION_RELAY_RESPONSE]` with the user's answer back to the subagent.
2. **Subagent Timeout Mitigation**:
   - Subagents blocked on interactive user questions risk timeouts or UI occlusion when running nested under orchestrators.
   - Elevating questions to the session root orchestrator ensures prompt rendering is visible to the user and avoids subagent timeouts.
   - Subagents maintain execution state cleanly, awaiting the single `[QUESTION_RELAY_RESPONSE]` message.
3. **Standalone Fallback**: Subagents maintain a fallback to invoke `ask_question` directly when invoked standalone outside of the `@coding` orchestrator.
