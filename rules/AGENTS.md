# Coding Standards & Guidelines — agentic-coding-plugin

This rule set applies whenever the `agentic-coding-plugin` is active in an Antigravity session.

---

## 1. Core Engineering Principles
- **Clarity over Cleverness**: Write readable, expressive code with self-explanatory naming and explicit typing.
- **Fail Fast & Explicitly**: Validate boundaries, function arguments, and I/O operations early.
- **Single Responsibility**: Functions and classes should have one well-defined responsibility.
- **Preserve Comments & Docstrings**: Never strip existing comments or docstrings unless explicitly instructed.

---

## 2. Code Review & Verification
- Verify all code changes with relevant automated tests or dry runs before concluding a task.
- When repositories contain local deployment instructions (Docker, Compose, Minikube, Terraform, scripts), execute and monitor local deployment via `@coding-deploy` after development before code review and merge.
- When creating or editing files, create clickable file and symbol links in markdown responses using the `file://` scheme.
- Adhere to the language idioms and clean architecture boundaries of the host project.

---

## 3. Communication & Style
- Keep responses concise and focused on high-signal findings.
- Use GitHub Flavored Markdown alerts (`> [!NOTE]`, `> [!IMPORTANT]`, `> [!TIP]`, `> [!WARNING]`) appropriately to emphasize key points without nesting.

---

## 4. Documentation Delegation & Obsidian Vault Integration
- When `agentic-project-documenting-plugin` is installed, all documentation tasks (project documentation, feature specifications, architecture designs, ADRs, session logs, and git status updates) must be delegated to `@coding-document`.
- `@coding` must invoke `@coding-document` to maintain documentation only after:
  - **After the Plan is Approved**: Document architecture designs, work breakdowns, approved feature specifications, and formalize ADRs.
  - **Before Merging (Pre-Merge)**: Perform pre-merge documentation tidy-up across READMEs, architecture records, and feature specs upon merge confirmation.
  - **At the End (Post-Merge)**: Update repository git statuses (`agentic-obsidian/git-status.md`), branch topologies, and release changelogs once merge concludes.
- If `agentic-project-documenting-plugin` is not installed, skip the documentation invocation and advance directly to the subsequent phase.

---

## 5. Companion Subagents & Delegation
- **Local Deployment & Health Monitoring**: Local deployment execution and monitoring is handled by `@coding-deploy`.
- **Issue Investigation**: Complex root-cause diagnosis, defect tracing, and fix proposals are handled by `@coding-investigate` (`agentic-issue-investigation-plugin`).
- **Telemetry & Stream Surveillance**: Real-time log, container, and serial stream monitoring is handled by `@coding-monitor` (`agentic-task-monitoring-plugin`).
- **Topic & Literature Research**: Deep web research, technical literature synthesis, and documentation lookups are handled by `@coding-research` (`agentic-topic-researching-plugin`).
- **Project Grooming**: Scope boundary clarification, backlog grooming, and repository bootstrapping are handled via `/project-grooming` (`agentic-project-grooming-plugin`).
- **Prompt Triage**: Request classification and intent routing are handled by the dynamic triage hook (`agentic-prompt-triage-plugin`).

---

## 6. Question Relay Protocol & Interactive Gates
- **Question Delegation**: When running under `@coding` (caller ID present), worker subagents (`@coding-clarify`, `@coding-deploy`, `@coding-review`, `@coding-merge`) must not execute user-prompting tools (`ask_question`) directly.
- **Contract Format**: Subagents must relay questions to the parent orchestrator using `send_message` with `[QUESTION_RELAY_REQUEST]\nQuestion: ...\nOptions: ...\nContext: ...`. The parent orchestrator prompts the user at the session root via `ask_question` and replies to the subagent with `[QUESTION_RELAY_RESPONSE]\nAnswer: ...`.
- **Subagent Timeout Mitigation**: Relaying questions to the root orchestrator ensures prompt visibility in the main UI stream and mitigates subagent timeouts caused by deep nested interaction blocking.
- **Standalone Fallback**: If a worker subagent is invoked as a standalone top-level agent without a caller ID, it falls back to calling `ask_question` directly.

---

## 7. Artifact Approval Relay Protocol & Approval Gates
- **Artifact Approval Delegation**: When running under `@coding` (caller ID present), worker subagents (`@coding-specify`, `@coding-plan`, `@coding-deploy`) must NOT author artifacts with `RequestFeedback=True` directly. Doing so inside background worker processes triggers Antigravity's 60-second subagent execution timeout when users take longer than 60 seconds to review.
- **Worker Execution Flow**:
  1. Author artifact directly to disk using `write_file(Path=artifact_path, Content=..., Overwrite=True)` without `ArtifactMetadata` or with `RequestFeedback=False`.
  2. Dispatch `[ARTIFACT_APPROVAL_REQUEST]` to `caller_id` via `send_message`.
  3. Enter idle state and await reactive wakeup upon receiving `[ARTIFACT_APPROVAL_RESPONSE]`.
- **Orchestrator Handling (`@coding`)**:
  1. Intercepts `[ARTIFACT_APPROVAL_REQUEST]`, inspects the artifact on disk, and presents it to the user by calling `write_file(Path=artifact_path, Content=..., Overwrite=True, ArtifactMetadata={"RequestFeedback": True, "UserFacing": True, "Summary": ...})` as the **sole and final tool call of that turn**.
  2. Awaits interactive user decision at the session root without background execution timeouts.
  3. Relays user outcome (`APPROVED` or `REJECTED` with feedback) back to the subagent using `[ARTIFACT_APPROVAL_RESPONSE]` via `send_message`.
- **Standalone Fallback**: If a worker subagent is invoked as a standalone top-level agent without a caller ID, it authors the artifact directly with `RequestFeedback=True` as the sole and final tool call of the turn.

