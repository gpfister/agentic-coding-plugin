# Contributing to agentic-coding-plugin

Thank you for your interest in contributing to **`agentic-coding-plugin`**! This plugin is the primary coding companion within the `agentic` workspace, providing declarative markdown-defined subagents, progressive-disclosure skills, and clean engineering standards for Google Antigravity.

Please review this document to understand our development workflows, code standards, and submission guidelines.

---

## 1. Core Principles & Philosophy

Whenever developing or extending this plugin, uphold the core engineering tenets defined in [`rules/AGENTS.md`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/rules/AGENTS.md):

- **Clarity over Cleverness**: Write readable, expressive, and type-annotated code with self-explanatory names.
- **Fail Fast & Explicitly**: Validate function boundaries, inputs, and environment pre-conditions early.
- **Single Responsibility**: Each subagent and Python utility should focus on one well-defined responsibility.
- **Preserve Comments & Docstrings**: Never remove or compress existing documentation or docstrings unless explicitly instructed.
- **Clickable File Links**: Use Markdown links formatted with the `file://` scheme when referencing local files and symbols.

---

## 2. Environment Setup

### Prerequisites
- **Python**: 3.11 or newer (Python 3.13 recommended)
- **uv**: Fast Python package manager ([Astral `uv`](https://astral.sh/uv))
- **Git**: 2.30+

### Setup Steps
1. Clone or navigate to the repository:
   ```bash
   cd agentic-coding-plugin
   ```
2. Provision the virtual environment and install dependencies via the post-install script:
   ```bash
   ./scripts/post_install.sh
   ```
3. Verify that the test suite passes:
   ```bash
   .venv/bin/pytest -v
   ```

---

## 3. Repository Architecture

```text
agentic-coding-plugin/
├── agents/             # Declarative markdown subagent specifications
│   ├── agent.md        # Central subagents directory & workflow specification
│   ├── coding/         # Stage orchestrator (@coding)
│   ├── coding-deploy/  # Local deployment worker (@coding-deploy)
│   └── coding-*/       # Worker subagents (clarify, specify, plan, develop, review, merge)
├── plugin.json         # Plugin manifest
├── pyproject.toml      # Project configuration and uv dependencies
├── rules/              # Plugin-scoped rules
│   └── AGENTS.md       # Active coding standards
├── scripts/            # Automation scripts (post_install.sh)
├── skills/             # On-demand progressive skills
│   ├── clean-code-reviewer/
│   └── coding-orchestrator/
├── tests/              # Pytest test suite
├── LICENSE             # MIT License
├── CONTRIBUTING.md     # Contribution guidelines (this file)
└── README.md           # Plugin overview
```

---

## 4. How to Contribute

### 4.1 Reporting Issues & Feature Proposals
- Check existing issues and session logs in `agentic-obsidian/sessions/` to see if the topic has been discussed.
- Open an issue describing the bug, unexpected behavior, or proposed enhancement with clear reproduction steps.

### 4.2 Branching Model
- Create a feature branch from `master`:
  ```bash
  git checkout -b feature/your-feature-name
  ```
  or for bug fixes:
  ```bash
  git checkout -b bugfix/your-fix-name
  ```

### 4.3 Adding or Modifying Subagents
1. Create a dedicated directory under [`agents/<agent-name>/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/) with `agent.md`.
2. Ensure the frontmatter contains `name`, `description`, `enable_write_tools`, `enable_subagent_tools`, `enable_mcp_tools`, and `tools`:
   ```markdown
   ---
   name: my-agent
   description: Concise description of the agent role and triggering circumstances.
   enable_write_tools: true
   enable_subagent_tools: false
   enable_mcp_tools: true
   tools:
     - read_file
     - write_file
   ---
   ```
3. Update the central catalog in [`agents/agent.md`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/agents/agent.md).
4. Update tests in [`tests/test_plugin.py`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/tests/test_plugin.py).

### 4.4 Adding or Modifying Skills
1. Create a directory [`skills/<skill-name>/`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/skills/).
2. Provide a [`SKILL.md`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/skills/) with YAML frontmatter (`name`, `description`).
3. Add a test in [`tests/test_plugin.py`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/tests/test_plugin.py) verifying the skill exists and adheres to formatting.

---

## 5. Coding & Commit Standards

- **Commit Messages**: Follow [Conventional Commits](https://www.conventionalcommits.org/):
  - `feat(agents): add coding-deploy subagent`
  - `docs: update CONTRIBUTING.md and README.md`
  - `test(plugin): add verification for coding-deploy`
- **Formatting & Typing**:
  - Keep Python code formatted cleanly and with type hints (`typing` or `from __future__ import annotations`).
  - Keep dependency specifications minimal in [`pyproject.toml`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/pyproject.toml).

---

## 6. Pull Request Checklist

Before submitting a Pull Request:
- [ ] Virtual environment generated with `./scripts/post_install.sh`.
- [ ] All automated tests pass: `.venv/bin/pytest -v`.
- [ ] Manifest [`plugin.json`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/plugin.json) and [`pyproject.toml`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/pyproject.toml) are valid and synchronized.
- [ ] Documentation and specifications in `agentic-obsidian/plugins/agentic-coding-plugin.md` are updated if public interfaces or protocols changed.
- [ ] Clickable links use `file://` scheme where applicable.

---

## 7. License

By contributing to `agentic-coding-plugin`, you agree that your contributions will be licensed under the [MIT License](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/LICENSE).
