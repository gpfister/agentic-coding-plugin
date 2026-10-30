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
- When creating or editing files, create clickable file and symbol links in markdown responses using the `file://` scheme.
- Adhere to the language idioms and clean architecture boundaries of the host project.

---

## 3. Communication & Style
- Keep responses concise and focused on high-signal findings.
- Use GitHub Flavored Markdown alerts (`> [!NOTE]`, `> [!IMPORTANT]`, `> [!TIP]`, `> [!WARNING]`) appropriately to emphasize key points without nesting.

---

## 4. Documentation Delegation & Obsidian Vault Integration
- When `agentic-document-plugin` (or `agentic-obsidian-plugin`) is installed, all documentation tasks (project documentation, feature specifications, architecture designs, ADRs, session logs, and git status updates) must be delegated to `@coding-document`.
- `@coding` must invoke `@coding-document` to maintain documentation after each phase:
  - **After Phase 1 (Clarify)**: Document clarified requirements, scope bounds, and interview outcomes.
  - **After Phase 2 (Specify)**: Document and index the approved `specification.md` into vault feature notes.
  - **After Phase 3 (Plan)**: Document architecture designs, work breakdowns, and formalize ADRs.
  - **After Phase 4 (Develop)**: Document implementation details, code changes, and test verification reports.
  - **After Phase 5 (Review / Pre-Merge)**: Perform pre-merge documentation tidy-up across READMEs, architecture records, and feature specs.
  - **After Phase 6 (Merge / Post-Merge)**: Update repository git statuses (`agentic-obsidian/git-status.md`), branch topologies, and release changelogs.
- If `agentic-document-plugin` (or `agentic-obsidian-plugin`) is not installed, skip the documentation invocation and advance directly to the subsequent phase.
