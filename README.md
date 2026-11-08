# agentic-coding-plugin

A Google Antigravity companion plugin for high-quality software engineering and clean code review.

## Contents

- **`plugin.json`**: Plugin manifest declaring metadata and post-install scripts.
- **`pyproject.toml`**: Package specification and testing dependencies managed via `uv`.
- **`scripts/post_install.sh`**: Post-installation script that runs `uv sync` to provision `.venv`.
- **`agents/`**: Declarative subagent definitions for the 7-stage lifecycle (`@coding`, `@coding-clarify`, `@coding-specify`, `@coding-plan`, `@coding-develop`, `@coding-deploy`, `@coding-review`, `@coding-merge`).
- **`rules/AGENTS.md`**: Core engineering principles, testing constraints, and code style rules applied whenever this plugin is active.
- **`skills/coding-orchestrator/`**: Progressive skill orchestrating full-lifecycle software delivery.
- **`skills/clean-code-reviewer/`**: Progressive skill for auditing codebases for anti-patterns, code smells, and architecture boundaries.
- **`CONTRIBUTING.md`**: Contribution guidelines, development workflows, and checklists.
- **`LICENSE`**: MIT License.

---

## Architecture & Subagents

The `agentic-coding-plugin` coordinates a 7-stage development lifecycle:

1. **Clarification (`@coding-clarify`)**: Interrogates edge cases and dependencies one question at a time.
2. **Specification (`@coding-specify`)**: Authors `specification.md` with interactive approval gate.
3. **Planning (`@coding-plan`)**: Breaks down tasks, assesses local deployment, and plans git branches in `plan.md` with interactive approval gate.
4. **Development (`@coding-develop`)**: Parallel implementation workers per repository.
5. **Local Deployment (`@coding-deploy`)**: Executes and monitors local deployment (Docker, Minikube, Terraform, scripts) per repo, investigating errors and authoring `Deployment Issue` artifacts with remediation options on failure.
6. **Review (`@coding-review`)**: Audits changes and deployment health against specification and verifies tests.
7. **Release & Merge (`@coding-merge`)**: Merges locally with base branch switch verification and safe local branch deletion, or creates GitHub pull requests with interactive Question Relay waiting gates, post-merge base synchronization (`git pull --ff-only`), remote branch deletion (`git push origin --delete`), local branch deletion (`git branch -d`), and remote tracking reference pruning (`git fetch --prune origin`).

### Release & Merge Hygiene (`@coding-merge`)

To eliminate repository branch clutter, stale tracking references, and detached working trees:
- **Local Release Strategy**: When no remote is configured, checks out the base branch (`main`/`master`), merges the feature branch (`git merge <branch>`), verifies checkout on the base branch (`git branch --show-current`), and safely deletes the local feature branch (`git branch -d <branch>`), emitting `MergeReport` with `cleanup: true`.
- **Remote Release Strategy**: Pushes the feature branch (`git push -u origin <branch>`), creates a Pull Request via GitHub CLI (`gh pr create` with browser compare URL fallback), and delegates PR review waiting gates to the parent caller via Question Relay Protocol (`[QUESTION_RELAY_REQUEST]`). Once merged, switches to the base branch (`git checkout <base>`), fast-forwards remote commits (`git pull --ff-only origin <base>`), deletes the remote feature branch (`git push origin --delete <branch>`), safely deletes the local feature branch (`git branch -d <branch>`), prunes obsolete remote-tracking references (`git fetch --prune origin`), and verifies the working tree confirms the base branch.

### Dual-Mode Orchestration & Multi-Hop Relay Protocol

To eliminate duplicate interactive UI approval gates and the rigid **60-second runtime execution timeout** enforced on background subagents in Google Antigravity:
- **Subagent Mode (`caller_id` present)**: When `@coding` is invoked by an upstream agent (e.g., `@coding-investigate`, `/project-grooming`, or root orchestrator), it acts as a child subagent. It **MUST NOT** invoke `write_file(RequestFeedback=True)` or `ask_question`. Instead, it operates as a **Multi-Hop Relay**: forwarding worker subagent `[ARTIFACT_APPROVAL_REQUEST]` and `[QUESTION_RELAY_REQUEST]` envelopes upward to `caller_id` via `send_message`, yielding immediately to await `[ARTIFACT_APPROVAL_RESPONSE]` or `[QUESTION_RELAY_RESPONSE]`, and routing responses downward to the waiting subagent.
- **Standalone Mode (no `caller_id`)**: When `@coding` is invoked directly by the user at the session root, it acts as the primary gatekeeper: rendering `write_file(RequestFeedback=True)` directly as the sole and final tool call of that turn for artifact review, and calling `ask_question` directly for user clarification.

### Hard Anti-Direct-Coding Guardrails

To preserve architectural integrity and prevent the orchestrator from bypassing the 7-stage lifecycle upon receiving imperative fix requests:
- `@coding` is strictly a meta-orchestrator and **MUST NEVER** write, edit, or delete application source code, configuration files, Makefiles, or test suites directly.
- `write_file` is strictly restricted to presenting interactive milestone artifacts (`<appDataDir>/brain/<id>/*.md`) in Standalone Mode.
- `run_command` is strictly restricted to read-only workspace inspection (`git status`).
- 100% of implementation is delegated to `@coding-develop`, local deployment checks to `@coding-deploy`, code review to `@coding-review`, and merges/PRs to `@coding-merge`.

### Pre-Clarified Fast-Path

When `@coding` is invoked with pre-clarified requirements, an approved architecture document, or an approved issue assessment report from companion subagents:
- Phase 1 (`coding-clarify`) is skipped automatically.
- Workflow fast-paths directly to Phase 2 (`coding-specify`) or Phase 3 (`coding-plan`).
- Formal approval gates (`specification.md`, `plan.md`) remain mandatory before any code development is initiated.

### Question Relay Protocol (Subagent User Inquiries)

To eliminate the strict **60-second runtime execution timeout** enforced on background subagents in Google Antigravity:
- Subagents (`@coding-clarify`, `@coding-deploy`, `@coding-review`, `@coding-merge`) do not prompt the user directly via `ask_question`. Instead, they dispatch a structured `[QUESTION_RELAY_REQUEST]` envelope via `send_message` to the parent orchestrator (`@coding`) and enter an idle state.
- The top-level orchestrator (`@coding` in standalone mode, or root caller via multi-hop relay in subagent mode) intercepts the request, runs `ask_question` at the session root without host timeouts (allowing unlimited user deliberation time), and returns the selected answer in a `[QUESTION_RELAY_RESPONSE]` envelope.
- The subagent wakes up reactively upon message delivery and advances its workflow.

### Companion Plugins & Ecosystem Subagents

This plugin collaborates seamlessly with companion plugins in the `agentic` workspace:
- **`@coding-deploy`**: Autonomous local deployment execution, health monitoring, error diagnosis, and self-healing.
- **`@coding-investigate`** ([`agentic-issue-investigation-plugin`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-issue-investigation-plugin)): Autonomous multi-repo root cause diagnosis and issue resolution.
- **`@coding-monitor`** ([`agentic-task-monitoring-plugin`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-task-monitoring-plugin)): Telemetry, log surveillance, and Docker stream observation.
- **`@coding-document`** ([`agentic-project-documenting-plugin`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-project-documenting-plugin)): Centralized Obsidian documentation vault maintenance.
- **`@coding-research`** ([`agentic-topic-researching-plugin`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-topic-researching-plugin)): Autonomous web and literature research briefs.
- **`/project-grooming`** ([`agentic-project-grooming-plugin`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-project-grooming-plugin)): Interactive project initialization, backlog grooming, and scope boundary interrogation.
- **`Prompt Triage`** ([`agentic-prompt-triage-plugin`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-prompt-triage-plugin)): Dynamic non-autoregressive prompt classification and intent routing.

---

## Contributing

See [CONTRIBUTING.md](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/CONTRIBUTING.md) for details on branching, subagent authoring, testing, and pull requests.

## License

This project is licensed under the [MIT License](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/LICENSE).

---

## Installation & Setup

### 1. Provision Virtual Environment
Run the automated post-install script (requires `uv`):

```bash
./scripts/post_install.sh
```

This creates `.venv` and installs development dependencies.

### 2. Enable Plugin in Antigravity
```bash
agy plugin enable agentic-coding-plugin
```

### 3. Run Automated Tests
```bash
.venv/bin/pytest tests/test_plugin.py -v
```
