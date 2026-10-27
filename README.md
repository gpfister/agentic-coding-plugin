# agentic-coding-plugin

A Google Antigravity companion plugin for high-quality software engineering and clean code review.

## Contents

- **`plugin.json`**: Plugin manifest declaring metadata and post-install scripts.
- **`pyproject.toml`**: Package specification and testing dependencies managed via `uv`.
- **`scripts/post_install.sh`**: Post-installation script that runs `uv sync` to provision `.venv`.
- **`rules/AGENTS.md`**: Core engineering principles, testing constraints, and code style rules applied whenever this plugin is active.
- **`skills/clean-code-reviewer/`**: Progressive skill for auditing codebases for anti-patterns, code smells, and architecture boundaries.
- **`CONTRIBUTING.md`**: Contribution guidelines, development workflows, and checklists.
- **`LICENSE`**: MIT License.

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
