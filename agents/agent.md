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
| **`@coding`** | [`agents/coding/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/coding/) | `True` | `True` | `True` | `invoke_subagent`, `send_message`, `manage_subagents`, `ask_question`, `read_file`, `write_file`, `list_dir`, `run_command` | Dual-Mode 7-stage lifecycle pipeline orchestration with multi-hop relay and constrained tools (write_file strictly for standalone gates, run_command for status inspection) |
| **`@coding-clarify`** | [`agents/coding-clarify/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/coding-clarify/) | `False` | `False` | `True` | `ask_question`, `read_file`, `list_dir`, `search_web`, `send_message` | One-question-at-a-time requirement interrogation with Question Relay Protocol |
| **`@coding-specify`** | [`agents/coding-specify/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/coding-specify/) | `True` | `False` | `True` | `write_file`, `read_file`, `list_dir`, `search_web`, `send_message` | Specification authoring & interactive approval gate |
| **`@coding-plan`** | [`agents/coding-plan/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/coding-plan/) | `True` | `False` | `True` | `write_file`, `read_file`, `list_dir`, `run_command`, `send_message` | Multi-repo task breakdown, deployment assessment, & branch planning |
| **`@coding-develop`** | [`agents/coding-develop/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/coding-develop/) | `True` | `False` | `True` | `read_file`, `write_file`, `edit_file`, `list_dir`, `run_command`, `search_web` | Isolated repo implementation, tests, linting, docs, and fix remediation |
| **`@coding-deploy`** | [`agents/coding-deploy/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/coding-deploy/) | `True` | `True` | `True` | `run_command`, `read_file`, `list_dir`, `write_file`, `edit_file`, `ask_question`, `send_message`, `invoke_subagent` | Local deployment execution, health monitoring, error investigation & fix orchestration |
| **`@coding-review`** | [`agents/coding-review/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/coding-review/) | `True` | `False` | `True` | `read_file`, `list_dir`, `run_command`, `ask_question`, `send_message` | Deliverables and deployment verification against specification; merge confirmation relay |
| **`@coding-merge`** | [`agents/coding-merge/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/coding-merge/) | `True` | `False` | `True` | `run_command`, `read_file`, `list_dir`, `ask_question`, `send_message` | Local branch merge or remote Pull Request creation with Question Relay waiting gate and post-merge branch sync |

### 1.3 Dual-Mode Orchestration & Anti-Direct-Coding Boundaries
- **Pure Subagents vs Dual-Mode Orchestrator**:
  - **Pure Subagents** (`@coding-clarify`, `@coding-specify`, `@coding-plan`, `@coding-develop`, `@coding-deploy`, `@coding-review`, `@coding-merge`): Strictly run under `@coding`. They never execute `ask_question` directly or author artifacts with `RequestFeedback=True` when under orchestrator control; all interactions are relayed via `[QUESTION_RELAY_REQUEST]` and `[ARTIFACT_APPROVAL_REQUEST]`.
  - **Dual-Mode Orchestrator (`@coding`)**:
    * **Subagent Mode (`caller_id` present)**: When `@coding` is invoked by an upstream orchestrator, it intercepts requests from child subagents and relays `[QUESTION_RELAY_REQUEST]` and `[ARTIFACT_APPROVAL_REQUEST]` upward to `caller_id` via `send_message`. It **MUST NOT** invoke `ask_question` or `write_file(RequestFeedback=True)`, avoiding background execution timeouts and duplicate interactive UI gates.
    * **Standalone Mode (no `caller_id`)**: When invoked at the root session, `@coding` presents interactive approval gates via `write_file(RequestFeedback=True)` as the sole tool call of that turn, or prompts the user directly via `ask_question`.
- **Anti-Direct-Coding Guardrails**:
  - `@coding` is strictly a meta-orchestrator and **MUST NEVER** write, edit, or delete application source code, configuration files, Makefiles, build scripts, or test suites directly.
  - `write_file` is strictly restricted to presenting interactive approval gates (`<appDataDir>/brain/<id>/*.md`) in Standalone Mode.
  - `run_command` is strictly restricted to non-destructive workspace inspection queries (e.g. `git status`). All development is delegated strictly to `@coding-develop`.
- **Pre-Clarified Fast-Path**:
  - When `@coding` is invoked with pre-clarified requirements, an approved architecture document, or an approved issue assessment report, it skips Phase 1 (`coding-clarify`) and fast-paths directly to Phase 2 (`coding-specify`) or Phase 3 (`coding-plan`). Approval gates are strictly preserved before development.

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
- **Artifact Approval Relay Gate**:
  - `coding-specify` writes `specification.md` to disk without `RequestFeedback=True`.
  - Dispatches `[ARTIFACT_APPROVAL_REQUEST]` to `@coding` and awaits `[ARTIFACT_APPROVAL_RESPONSE]`.
  - In Subagent Mode, `@coding` forwards `[ARTIFACT_APPROVAL_REQUEST]` directly to `caller_id` via `send_message`. In Standalone Mode, `@coding` presents the interactive modal to the user using `write_file(..., ArtifactMetadata={"RequestFeedback": True, "UserFacing": True})` as its sole tool call of that turn, avoiding subagent timeouts.
  - `@coding` advances to Stage 3 (`coding-plan`) upon receiving approval (or routes to `coding-clarify` on rejection).

### Stage 3: Planning (`coding-plan`)
- **Objective**: Deconstruct the approved specification into atomic, verifiable steps, assess local deployment requirements, and determine git branch names (`plan.md`).
- **Local Deployment Assessment**:
  - `coding-plan` inspects each target repository for local deployment mechanisms (Docker, docker-compose, scripts/deployment_local.sh, terraform/local, Minikube/Kubernetes manifests).
  - Explicitly adds local deployment tasks for repositories requiring them.
- **Multi-Repository Isolation**:
  - Assigns work strictly per repository (respecting workspace boundaries).
  - Branch conventions: `feature/<name>` (new capabilities), `task/<name>` (maintenance/refactoring), `bugfix/<name>` (bug fixes).
- **Artifact Approval Relay Gate**:
  - `coding-plan` writes `plan.md` to disk without `RequestFeedback=True`.
  - Dispatches `[ARTIFACT_APPROVAL_REQUEST]` to `@coding` and awaits `[ARTIFACT_APPROVAL_RESPONSE]`.
  - In Subagent Mode, `@coding` forwards `[ARTIFACT_APPROVAL_REQUEST]` directly to `caller_id` via `send_message`. In Standalone Mode, `@coding` presents the interactive modal to the user using `write_file(..., ArtifactMetadata={"RequestFeedback": True, "UserFacing": True})` as its sole tool call of that turn.
  - `@coding` advances to Stage 4 (`coding-develop`) upon receiving approval (or routes to `coding-clarify` on rejection).

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
    2. Author a `Deployment Issue` artifact (`deployment-issue.md`) without `RequestFeedback=True` and dispatch `[ARTIFACT_APPROVAL_REQUEST]` to `@coding`.
    3. In Subagent Mode, `@coding` forwards `[ARTIFACT_APPROVAL_REQUEST]` directly to `caller_id` via `send_message`. In Standalone Mode, `@coding` presents the artifact to the user via `write_file(..., ArtifactMetadata={"RequestFeedback": True, "UserFacing": True})` and relays `[ARTIFACT_APPROVAL_RESPONSE]`.
    4. If approved: if multiple solutions were proposed, prompt the user to choose the desired fix (relaying upward via `[QUESTION_RELAY_REQUEST]` in Subagent Mode, or calling `ask_question` directly in Standalone Mode).
    5. Invoke `coding-develop` to implement the approved fix.
    6. Re-deploy and verify health until clean or user aborts.
- **Handoff**: Concludes with structured `DeployReport` JSON.

### Stage 6: Review (`coding-review`)
- **Objective**: Validate all deliverables against the original specification, verify cross-repo contract compatibility, and confirm that all required local deployments succeeded.
- **Discrepancy Routing**:
  - If regressions or specification discrepancies are found: Route issues back to `coding-plan` via `@coding` with actionable feedback.
  - If approved: Present validation summary to the user and request confirmation to proceed to merge (relaying upward via `[QUESTION_RELAY_REQUEST]` in Subagent Mode, or handled directly by `@coding` via `ask_question` in Phase 6 in Standalone Mode).

### Stage 7: Release & Merge (`coding-merge`)
- **Objective**: Safely integrate approved changes into repository release branches.
- **Prerequisite**: `@coding-merge` strictly waits for all `coding-deploy` and all `coding-develop` tasks to have completed successfully before proceeding.
- **Merge Strategy**:
  - **No Remote Repository (Local Strategy)**: Checkout base branch (`master`/`main`) and execute local `git merge <branch>`.
  - **Remote Repository Configured (Remote Strategy)**:
    - Push feature branch to origin: `git push -u origin <branch>`.
    - Check GitHub CLI authentication status: `gh auth status`.
    - If authenticated, create Pull Request: `gh pr create --base <base> --head <branch> --title "<title>" --body "<body>"`.
    - If unauthenticated or missing `gh`, generate web compare URL (`https://github.com/<owner>/<repo>/compare/<base>...<branch>?expand=1`) and prompt user via Question Relay Protocol.
    - **Hybrid PR Waiting Gate**: Inspect PR state via `gh pr view <pr_number> --json state,reviewDecision,mergedAt,url`. If `state == "OPEN"`, delegate gate choices to `@coding` using `[QUESTION_RELAY_REQUEST]` (Re-check, Enable GitHub auto-merge, or Proceed without waiting) to prevent Antigravity 60-second subagent timeouts.
    - **Post-Merge Base Synchronization & Local Cleanup**: When PR is merged (`state == "MERGED"`), switch to base branch (`git checkout <base>`), pull remote changes fast-forward (`git pull --ff-only origin <base>`), and delete local feature branch (`git branch -d <branch>`).

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

## 4. Artifact Approval Relay Protocol (`[ARTIFACT_APPROVAL_REQUEST]` / `[ARTIFACT_APPROVAL_RESPONSE]`)

In Google Antigravity, background worker subagents run inside managed subagent processes with a strict 60-second turn execution timeout. If a subagent invokes `write_file` with `ArtifactMetadata={"RequestFeedback": True}`, the subagent process remains active waiting for the user to review and interact with the Approve / Reject buttons. If the user deliberates for longer than 60 seconds, Antigravity throws a subagent execution timeout error, crashing the workflow.

To eliminate this timeout while preserving full human-in-the-loop interactive control, artifact approval gates are relayed through the top-level orchestrator (`@coding`):

### 4.1 Protocol Message Envelopes

#### Request: `[ARTIFACT_APPROVAL_REQUEST]`
Dispatched by the worker subagent (`coding-specify`, `coding-plan`, `coding-deploy`) to `@coding` (`caller_id`):
```text
[ARTIFACT_APPROVAL_REQUEST]
```
```json
{
  "type": "ARTIFACT_APPROVAL_REQUEST",
  "artifact_name": "specification.md",
  "artifact_path": "/Users/user/.gemini/antigravity/brain/<session-id>/specification.md",
  "stage": "SPECIFICATION",
  "summary": "Detailed technical specification for feature XYZ",
  "user_facing": true
}
```

#### Response: `[ARTIFACT_APPROVAL_RESPONSE]`
Dispatched by `@coding` back to the worker subagent:
```text
[ARTIFACT_APPROVAL_RESPONSE]
```
```json
{
  "type": "ARTIFACT_APPROVAL_RESPONSE",
  "artifact_name": "specification.md",
  "status": "APPROVED",
  "feedback": ""
}
```
*(On rejection, `"status": "REJECTED"` and `"feedback"` contains user comments.)*

### 4.2 Lifecycle Flow & Roles
1. **Worker Subagent**:
   - Writes the artifact to disk (`<appDataDir>/brain/<conversation-id>/<artifact_name>.md`) using `write_file(..., Overwrite=True)` without `ArtifactMetadata` or with `RequestFeedback=False`.
   - Sends `[ARTIFACT_APPROVAL_REQUEST]` via `send_message(Recipient="<caller_id>", Message=...)`.
   - Enters `idle` state and awaits reactive wakeup upon receiving `[ARTIFACT_APPROVAL_RESPONSE]`.
2. **Orchestrator Handling (`@coding`)**:
   - Intercepts `[ARTIFACT_APPROVAL_REQUEST]`.
   - **Subagent Mode (`caller_id` present)**: Forwards `[ARTIFACT_APPROVAL_REQUEST]` directly to `caller_id` via `send_message`. `@coding` **MUST NOT** invoke `write_file(RequestFeedback=True)` or present local approval gates. Halts turn immediately to await `[ARTIFACT_APPROVAL_RESPONSE]` from `caller_id`, then forwards it down to the child subagent.
   - **Standalone Mode (no `caller_id`)**: Reads the artifact content from disk at `artifact_path` and invokes `write_file(Path=artifact_path, Content=content, Overwrite=True, ArtifactMetadata={"RequestFeedback": True, "UserFacing": True, "Summary": summary})` as the **sole and final tool call of that turn** without subagent timeouts.
   - Relays the user decision back to the subagent using `[ARTIFACT_APPROVAL_RESPONSE]`.
3. **Standalone Fallback**:
   - If a subagent is invoked standalone without a caller ID, it writes the artifact directly with `ArtifactMetadata={"RequestFeedback": True, "UserFacing": True}` as its sole and final tool call.

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
1. **Multi-Hop Question Relay Handling**:
   - **Subagent Mode (`caller_id` present)**: Upon receiving `[QUESTION_RELAY_REQUEST]`, `@coding` forwards it upward to `caller_id` via `send_message` and yields turn immediately. `@coding` **MUST NOT** call `ask_question` directly. Once `[QUESTION_RELAY_RESPONSE]` is received from `caller_id`, `@coding` forwards it down to the child subagent.
   - **Standalone Mode (no `caller_id`)**: Upon receiving `[QUESTION_RELAY_REQUEST]`, `@coding` parses the question, options, and context, calls `ask_question` directly at the top level, and immediately sends `[QUESTION_RELAY_RESPONSE]` with the user's answer back to the subagent.
2. **Subagent Timeout Mitigation**:
   - Subagents blocked on interactive user questions risk timeouts or UI occlusion when running nested under orchestrators.
   - Elevating questions to the session root orchestrator ensures prompt rendering is visible to the user and avoids subagent timeouts.
   - Subagents maintain execution state cleanly, awaiting the single `[QUESTION_RELAY_RESPONSE]` message.
3. **Standalone Fallback**: Subagents maintain a fallback to invoke `ask_question` directly when invoked standalone outside of the `@coding` orchestrator.
