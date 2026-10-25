# Coding Standards & Guidelines — gp-coding-plugin

This rule set applies whenever the `gp-coding-plugin` is active in an Antigravity session.

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
