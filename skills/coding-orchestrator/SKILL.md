---
name: coding
description: >-
  Orchestrate full-lifecycle software development tasks through the 7-stage
  coordinated workflow: coding-clarify, coding-specify, coding-plan,
  coding-develop, coding-deploy, coding-review, and coding-merge.
---

# Coding Orchestrator (`@coding`)

The `coding` subagent guides software requests through a rigorous, multi-agent development pipeline.

## Workflow Pipeline & Flowchart

```mermaid
flowchart TD
    %% Top Entrypoint
    Start(["User Request / Task"]) --> P1["Phase 1: Clarification<br/>(@coding-clarify)"]
    
    %% Phase 1: Clarification
    P1 --> AmbiguityCheck{"Ambiguities or<br/>Open Questions?"}
    AmbiguityCheck -->|"Yes"| GrillUser["Relay Question to User<br/>([QUESTION_RELAY_REQUEST] -> ask_question<br/>-> [QUESTION_RELAY_RESPONSE])"]
    GrillUser --> P1
    AmbiguityCheck -->|"No / Clarified"| P2["Phase 2: Specification<br/>(@coding-specify)"]

    %% Phase 2: Specification
    P2 --> SpecSubagent["Write specification.md to disk<br/>Relay [ARTIFACT_APPROVAL_REQUEST]"]
    SpecSubagent --> SpecGateRoot["@coding calls write_file<br/>(RequestFeedback=True, sole tool call)"]
    SpecGateRoot --> SpecGate{"User Decision on<br/>specification.md?"}
    SpecGate -->|"Approved"| SpecApproved["Relay [ARTIFACT_APPROVAL_RESPONSE: APPROVED]<br/>Advance to Phase 3"]
    SpecGate -->|"Rejected"| SpecRejected["Relay [ARTIFACT_APPROVAL_RESPONSE: REJECTED]<br/>Route back to Phase 1"]
    SpecApproved --> P3["Phase 3: Planning<br/>(@coding-plan)"]
    SpecRejected --> P1

    %% Phase 3: Planning
    P3 --> PlanSubagent["Write plan.md to disk<br/>Relay [ARTIFACT_APPROVAL_REQUEST]"]
    PlanSubagent --> PlanGateRoot["@coding calls write_file<br/>(RequestFeedback=True, sole tool call)"]
    PlanGateRoot --> PlanGate{"User Decision on<br/>plan.md?"}
    PlanGate -->|"Approved"| PlanApproved["Relay [ARTIFACT_APPROVAL_RESPONSE: APPROVED]"]
    PlanGate -->|"Rejected"| PlanRejected["Relay [ARTIFACT_APPROVAL_RESPONSE: REJECTED]<br/>Route back to Phase 1"]
    PlanRejected --> P1
    PlanApproved --> DocPlanCheck{"agentic-project-documenting-plugin<br/>installed?"}
    DocPlanCheck -->|"Yes"| InvokeDocPlan["Invoke @coding-document<br/>(Document architecture plan & ADRs)"]
    DocPlanCheck -->|"No"| P4["Phase 4: Development<br/>(@coding-develop)"]
    InvokeDocPlan --> P4

    %% Phase 4: Development & Phase 5: Local Deployment (Per-Repo)
    P4 --> ParallelDev["Fan out parallel workers<br/>per repo on isolated branches"]
    ParallelDev --> DevWork["Implement code, tests, linting<br/>Return DevelopReport"]
    DevWork --> DeployCheck{"Local deployment<br/>instructions exist?"}
    DeployCheck -->|"Yes"| P5Deploy["Phase 5: Local Deployment<br/>(@coding-deploy per repo)"]
    DeployCheck -->|"No"| JoinDevDeploy["Synchronize Deliverables<br/>(All develop & deploy done)"]

    %% Phase 5: Deployment Execution, Monitoring & Error Loop
    P5Deploy --> DeployRun["Execute local deploy & monitor health"]
    DeployRun --> DeploySuccess{"Deployment<br/>Successful?"}
    DeploySuccess -->|"Yes"| JoinDevDeploy
    DeploySuccess -->|"Error"| DeployIssueSubagent["Investigate error, write deployment-issue.md<br/>Relay [ARTIFACT_APPROVAL_REQUEST]"]
    DeployIssueSubagent --> DeployIssueRoot["@coding calls write_file<br/>(RequestFeedback=True, sole tool call)"]
    DeployIssueRoot --> DeployGate{"User Decision on<br/>Deployment Issue?"}
    DeployGate -->|"Approved"| MultiSolCheck{"Multiple solutions<br/>proposed?"}
    MultiSolCheck -->|"Yes"| AskSol["Relay solution choice<br/>([QUESTION_RELAY_REQUEST] -> ask_question<br/>-> [QUESTION_RELAY_RESPONSE])"]
    MultiSolCheck -->|"Single"| InvokeFixDev["Invoke @coding-develop<br/>to implement fix"]
    AskSol --> InvokeFixDev
    InvokeFixDev --> P5Deploy
    DeployGate -->|"Rejected"| AbortWorkflow(["Abort / Terminate"])

    %% Phase 6: Review
    JoinDevDeploy --> P6Review["Phase 6: Review<br/>(@coding-review)"]
    P6Review --> AuditChanges["Audit deliverables & deployment<br/>Run verification test suites"]
    AuditChanges --> ReviewCheck{"Quality Audit<br/>Passed?"}
    ReviewCheck -->|"Passed"| MergeConfirmGate{"Confirm Merge with User<br/>(ask_question directly or relayed)"}
    MergeConfirmGate -->|"User Confirmed"| DocPreMergeCheck{"agentic-project-documenting-plugin<br/>installed?"}
    DocPreMergeCheck -->|"Yes"| InvokeDocPreMerge["Invoke @coding-document<br/>(Pre-merge tidy-up: update READMEs & architecture docs)"]
    DocPreMergeCheck -->|"No"| P7Merge["Phase 7: Merge & Release<br/>(@coding-merge)"]
    InvokeDocPreMerge --> P7Merge

    %% Phase 7: Release & Merge
    P7Merge --> ExecMerge["Wait for all develop & deploy<br/>Execute git merge or open GitHub PR"]
    ExecMerge --> DocPostMergeCheck{"agentic-project-documenting-plugin<br/>installed?"}
    DocPostMergeCheck -->|"Yes"| InvokeDocPostMerge["Invoke @coding-document<br/>(Post-merge: update git status, branch tracking & changelogs)"]
    DocPostMergeCheck -->|"No"| Complete(["Workflow Completed"])
    InvokeDocPostMerge --> Complete

    %% Rejection & Rework Loops (routing upward)
    SpecGate -->|"[GATE_REJECTED]"| P1
    PlanGate -->|"[GATE_REJECTED]"| P1
    ReviewCheck -->|"Defects Found"| P3

    %% User Denied Merge routes directly to bottom termination
    MergeConfirmGate -->|"User Denied"| AbortWorkflow
```

1. **`coding-clarify`**:
   - Conducts a Matt Pocock `/grill-me` style interview.
   - Clarifies edge cases, non-goals, and dependencies one question at a time using the Question Relay Protocol (`[QUESTION_RELAY_REQUEST]` / `[QUESTION_RELAY_RESPONSE]`).
   - Advances directly to `coding-specify` once all ambiguities are resolved.
2. **`coding-specify`**:
   - Synthesizes findings into `specification.md` and writes it to disk without `RequestFeedback=True`.
   - Dispatches `[ARTIFACT_APPROVAL_REQUEST]` to `@coding`.
   - Orchestrator inspects the artifact on disk and executes `write_file(..., ArtifactMetadata={"RequestFeedback": True, "UserFacing": True})` as its sole tool call of that turn to present the interactive modal to the user without subagent timeouts.
   - Upon user decision, orchestrator dispatches `[ARTIFACT_APPROVAL_RESPONSE]` back to `coding-specify`.
   - Advances to `coding-plan` on approval (or routes to `coding-clarify` on rejection).
3. **`coding-plan`**:
   - Decomposes work per repository and determines branch names (`feature/*`, `task/*`, `bugfix/*`).
   - Assesses if local deployment is required for each repository (Docker, Docker Compose, Terraform to local Kubernetes/Minikube, scripts).
   - Produces `plan.md` on disk without `RequestFeedback=True` and dispatches `[ARTIFACT_APPROVAL_REQUEST]` to `@coding`.
   - Orchestrator inspects the artifact on disk and executes `write_file(..., ArtifactMetadata={"RequestFeedback": True, "UserFacing": True})` as its sole tool call of that turn.
   - Upon user decision, orchestrator dispatches `[ARTIFACT_APPROVAL_RESPONSE]` back to `coding-plan`.
   - Advances to `coding-develop` on approval (or routes to `coding-clarify` on rejection).
   - **Post-Plan Approval Documentation**: If `agentic-project-documenting-plugin` is installed, invoke `@coding-document` after plan approval to document architecture plans, work breakdowns, and formalize ADRs.
4. **`coding-develop`**:
   - Fanned out in parallel per repository (`coding-develop-<repo>`).
   - Scoped strictly to each repo directory. Writes code, tests, documentation, and verifies linting.
   - Generates `DevelopReport`. Triggers `coding-deploy` immediately for repos with local deployment instructions.
5. **`coding-deploy`**:
   - Runs local deployment and actively monitors container health, pod states, and service endpoints.
   - On error, diagnoses root cause, writes `Deployment Issue` artifact (`deployment-issue.md`) without `RequestFeedback=True`, and dispatches `[ARTIFACT_APPROVAL_REQUEST]` to `@coding`.
   - Orchestrator calls `write_file(..., ArtifactMetadata={"RequestFeedback": True, "UserFacing": True})` as its sole tool call and returns `[ARTIFACT_APPROVAL_RESPONSE]` to `coding-deploy`.
   - If approved with multiple options, relays question to the user via `[QUESTION_RELAY_REQUEST]`.
   - Invokes `coding-develop` to implement the approved fix, then re-deploys and monitors.
6. **`coding-review`**:
   - Collects all develop and deploy reports. Confirms cross-repo consistency, spec compliance, and local deployment health.
   - If defects found, loops back to `coding-plan`. If approved, requests merge confirmation directly or via `[QUESTION_RELAY_REQUEST]`.
   - **Pre-Merge Documentation (Tidy Up)**: If `agentic-project-documenting-plugin` is installed, invoke `@coding-document` prior to merging to tidy up project and feature documentation, architecture diagrams, and ADRs.
7. **`coding-merge`**:
   - Waits for all `coding-develop` and all `coding-deploy` to complete successfully.
   - Automatically merges locally or opens a Pull Request with `gh` if remote exists.
   - **Post-Merge Documentation (At the End)**: If `agentic-project-documenting-plugin` is installed, invoke `@coding-document` at the end to update git status, branch states, and changelogs in the Obsidian vault.

## Question Relay Protocol & Subagent Timeout Mitigation

Worker subagents do not execute interactive user prompts directly when managed by `@coding`. Instead, they delegate interactive user queries to the parent orchestrator using structured message contracts:

### 1. Protocol Contracts
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

### 2. Orchestrator Handling & Timeout Mitigation Patterns
1. **Interactive Prompt Handling**: Upon receiving `[QUESTION_RELAY_REQUEST]`, the orchestrator parses the question, options, and context, calls `ask_question` at the top level, and immediately sends `[QUESTION_RELAY_RESPONSE]` with the user's answer back to the subagent.
2. **Subagent Timeout Mitigation**:
   - Subagents blocked on interactive user questions risk timeouts or UI occlusion when running nested under orchestrators.
   - Elevating questions to the session root orchestrator ensures prompt rendering is visible to the user and avoids subagent timeouts.
   - Subagents maintain execution state cleanly, awaiting the single `[QUESTION_RELAY_RESPONSE]` message.
3. **Standalone Fallback**: Subagents maintain a fallback to invoke `ask_question` directly when invoked standalone outside of the `@coding` orchestrator.

## Artifact Approval Relay Protocol & Approval Gates

To prevent background worker subagents from terminating due to Antigravity's 60-second subagent execution timeout when users review artifacts, artifact approval gates are relayed to the top-level orchestrator:

### 1. Protocol Envelopes
- **Approval Request (`Subagent -> @coding`)**:
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
- **Approval Response (`@coding -> Subagent`)**:
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

### 2. Orchestrator Handling Lifecycle
When `@coding` receives an `[ARTIFACT_APPROVAL_REQUEST]`:
1. **Inspect Artifact**: Read and inspect the artifact file at `artifact_path` on disk.
2. **Present Gate to User**: Call `write_file(Path=artifact_path, Content=content, Overwrite=True, ArtifactMetadata={"RequestFeedback": True, "UserFacing": True, "Summary": summary})` as the **sole and final tool call of that turn**.
3. **User Deliberation**: The orchestrator awaits user interaction (interactive Approve / Reject buttons). Because the orchestrator runs at the root session level, it is not subject to the 60-second subagent execution timeout.
4. **Relay Decision**: Upon receiving the user's decision:
   - On Approval: Dispatch `[ARTIFACT_APPROVAL_RESPONSE]` with `"status": "APPROVED"` to the worker subagent via `send_message`.
   - On Rejection / Feedback: Dispatch `[ARTIFACT_APPROVAL_RESPONSE]` with `"status": "REJECTED"` and `"feedback": "<comments>"` to the worker subagent via `send_message`.
5. **Stage Progression**:
   - For `specification.md`: on approval, advance to `coding-plan`; on rejection, route back to `coding-clarify`.
   - For `plan.md`: on approval, advance to `coding-develop`; on rejection, route back to `coding-clarify`.
   - For `deployment-issue.md`: on approval, handle solution selection and invoke `coding-develop`.

### 3. Idle Guard
- If a subagent enters `idle` while waiting for an approval response, Antigravity notifies `Subagent <id> has gone idle`.
- The orchestrator **MUST NOT** proceed to the next stage upon receiving `has gone idle`. It terminates its turn immediately without calling tools until the user responds.

## Triggering the Workflow

- Type `@coding <your feature or task description>`
- Or prompt: "Implement the following feature using the coding workflow: ..."
