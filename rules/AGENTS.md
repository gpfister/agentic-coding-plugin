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
- When `agentic-obsidian-plugin` is available, all documentation tasks (project documentation, feature specifications, architecture designs, ADRs, session logs, and git status updates) must be delegated to `@coding-document`.
- `@coding` must invoke `@coding-document`:
  - **Pre-Merge**: Prior to merging, to tidy up project documentation, feature specs, and architecture records.
  - **Post-Merge**: Immediately after merging, to update repository git statuses, branch states, and merge changelogs.
